import logging
from bisect import bisect_left
from datetime import datetime
import pandas as pd
from netCDF4 import Dataset, date2index
import geopy.distance

logger = logging.getLogger(__name__)


def read_ac_usage():
    usage_df: pd.DataFrame = pd.read_csv(r'data\ac_usage\38100019.csv')

    standalone_df = usage_df[lambda d: d['Air conditioners'] == 'Stand-alone air conditioner, as a percentage of all households']

    grouped = standalone_df[['REF_DATE', 'GEO', 'VALUE']].groupby('GEO')

    for group in grouped:
        print(group)


AC_CONSUMPTION: pd.DataFrame = pd.read_csv(r'data/ac_consumption/010_Data_Données.csv', encoding='windows-1252')


def get_ac_brands():
    return AC_CONSUMPTION["BRAND_NAME"].unique().tolist()


def get_models_for_brand(brand: str):
    return AC_CONSUMPTION[lambda d: d["BRAND_NAME"] == brand]['MODEL_NUM_1'].unique().tolist()


def get_ac_values(brand: str, model_name: str) -> (float, float):
    model_data = AC_CONSUMPTION[lambda d: (d['BRAND_NAME'] == brand) & (d['MODEL_NUM_1'] == model_name)]

    if len(model_data) == 0:
        logger.warning(f'AC {model_name} not found')
        return

    if len(model_data) > 1:
        logger.warning(f'Multiple AC {model_name} found, selecting first')

    ac = model_data.iloc[0]

    return ac['COOL_CAP_BTU'], ac['EE_RATIO']


_CDD_DATA = {}


def get_dataset_for_climate_model(model: str):
    global _CDD_DATA

    if model not in _CDD_DATA:
        _CDD_DATA[model] = Dataset(rf'data\cooling_degree_days\cdd_rcp{model}_ens-pct50_1951-2100.nc')

    return _CDD_DATA[model]


# TODO: which value for bisection?
# TODO: return distance from point
# model = 26, 45, 85
def get_location_cdd(lat: float, long: float, year: int, model: str) -> float:
    d = get_dataset_for_climate_model(model)
    # print(d)

    time = d['/time']
    time_idx = date2index(datetime(year, 1, 1, 0, 0), time)

    lats = d['/lat']
    lat_idx = bisect_left(lats[:], lat)

    longs = d['/lon']
    long_idx = bisect_left(longs[:], long)

    cdd = d['/cdd']

    return cdd[time_idx][lat_idx][long_idx]


ENERGY_RATES = {
    "QC": 0.100,
    "MN": 0.126,
    "BC": 0.160,
    "NB": 0.182,
    "AB": 0.201,
    "NL": 0.169,
    "SK": 0.232,
    "ON": 0.186,
    "NS": 0.230
}


def get_energy_rate(province) -> float:
    if province in ENERGY_RATES:
        return ENERGY_RATES[province]


_DESIGN_TEMP_STATIONS = pd.read_csv('data/records_df.csv')


# returns Celsius
def get_design_temp_and_station(coordinates):
    nearest_station = None
    nearest_station_distance = 1e10

    for idx, station_info in _DESIGN_TEMP_STATIONS.iterrows():
        station_coord = (station_info.lat, station_info.long)
        distance = geopy.distance.distance(coordinates, station_coord).km

        if distance < nearest_station_distance:
            nearest_station_distance = distance
            nearest_station = station_info

    design_temp_fahrenheit = nearest_station.design_temp
    design_temp = round((design_temp_fahrenheit - 32) * 5 / 9, 1)

    return nearest_station, nearest_station_distance, design_temp


def get_operation_cost(cdd, design_temp, cooling_cap_btu, ee_ratio, energy_rate):
    return 24 * (cdd / (design_temp - 18)) * (cooling_cap_btu / (ee_ratio * .9)) * (energy_rate / 1000)
