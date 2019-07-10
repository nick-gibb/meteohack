import logging
from math import radians, cos, sin, asin, sqrt
import csv
import requests

logger = logging.getLogger(__name__)


TIMEFRAMES = {'hourly': 1, 'daily': 2, 'monthly': 3}
AVG_EARTH_RADIUS = 6371  # km

DATE_TIME_TITLE = 'Date/Time'
TEMP_TITLE = 'Temp (°C)'
MEAN_TEMP_TITLE = 'Mean Temp (°C)'
TOTAL_PRECIP_TITLE = 'Total Precip (mm)'


_STATION_INV = {}


def get_station_inventory():
    global _STATION_INV

    if not _STATION_INV:
        with open(r'data\weather_station_inventory.csv', encoding='utf8') as stations_file:
            modified_date = stations_file.readline().strip()
            logger.info(f'Station Inventory {modified_date}')

            # skip disclaimers
            for _ in range(2):
                stations_file.readline()

            _STATION_INV = {station['Name']: station for station in csv.DictReader(stations_file)}

    return _STATION_INV


def stations_by_proximity(lat: float, long: float, radius_km=25) -> list:
    station_inv = get_station_inventory()

    stations = {}

    lat, long = map(radians, (lat, long))

    for station in station_inv:
        s = station_inv[station]

        s_lat = radians(float(s['Latitude (Decimal Degrees)']))
        s_long = radians(float(s['Longitude (Decimal Degrees)']))

        # haversine
        d = sin((s_lat - lat) / 2) ** 2 + cos(lat) * cos(s_lat) * sin((s_long - long) / 2) ** 2
        h = 2 * AVG_EARTH_RADIUS * asin(sqrt(d))

        if h <= radius_km:
            stations[station] = h

    return sorted(stations.items(), key=lambda kv: kv[1])


def station_dates(station_name: str):
    station_inv = get_station_inventory()

    info = station_inv[station_name]
    first_year, last_year = info['First Year'], info['Last Year']
    hourly_fy, hourly_ly = info['HLY First Year'], info['HLY Last Year']
    daily_fy, daily_ly = info['DLY First Year'], info['DLY Last Year']
    monthly_fy, monthly_ly = info['MLY First Year'], info['MLY Last Year']

    print(station_name, first_year, last_year)
    print('hourly', hourly_fy, hourly_ly)
    print('daily', daily_fy, daily_ly)
    print('monthly', monthly_fy, monthly_ly)

    if monthly_fy == '' or monthly_fy > first_year:
        print('gotta check earlier daily')
        if daily_fy == '' or daily_fy > first_year:
            print('gotta check earlier hourly')

    if monthly_ly == '' or monthly_ly < last_year:
        print('gotta check later daily')
        if daily_ly == '' or daily_ly < last_year:
            print('gotta check later hourly')

    print()


def full_monthly(station_name):
    info = get_station_inventory()[station_name]
    return info['MLY First Year'] == info['First Year'] and info['MLY Last Year'] == info['Last Year']


def full_daily(station_name):
    info = get_station_inventory()[station_name]
    return info['DLY First Year'] == info['First Year'] and info['DLY Last Year'] == info['Last Year']


# timeframes: monthly -> all data, daily -> full year, hourly -> full month
def bulk_data(station_id, year, month, timeframe):
    return 'http://climate.weather.gc.ca/climate_data/bulk_data_e.html?format=csv&' \
           f'stationID={station_id}&' \
           f'Year={year}&' \
           f'Month={month}&' \
           f'Day={1}&' \
           f'timeframe={timeframe}&' \
           'submit=Download+Data'


def data_rows(response_text: str):
    all_data = response_text.split('\n')

    # remove extraneous info
    current = all_data[0]
    while DATE_TIME_TITLE not in current:
        all_data.remove(current)
        current = all_data[0]

    return csv.DictReader(all_data)


def get_temp(record):
    temp = None

    if TEMP_TITLE in record:
        temp = record[TEMP_TITLE]
    elif MEAN_TEMP_TITLE in record:
        temp = record[MEAN_TEMP_TITLE]

    return temp if temp != '' else None


def get_precip(record):
    precip = None

    if TOTAL_PRECIP_TITLE in record:
        precip = record[TOTAL_PRECIP_TITLE]

    return precip if precip != '' else None


def get_hourly_data(station, year, month):
    response = requests.get(bulk_data(get_station_inventory()[station]['Station ID'], year, month, TIMEFRAMES['hourly']))

    return get_data_from_response(response)


def get_monthly_data(station):
    response = requests.get(bulk_data(get_station_inventory()[station]['Station ID'], 1970, 1, TIMEFRAMES['monthly']))

    return get_data_from_response(response)


def get_data_from_response(response):
    if response.status_code != 200:
        logger.warning(f'Error during climate data request: {response.status_code}')
        return

    temp_data, precip_data = {}, {}

    for record in data_rows(response.text):
        temp_data[record[DATE_TIME_TITLE]] = get_temp(record)
        precip_data[record[DATE_TIME_TITLE]] = get_precip(record)

    return temp_data, precip_data


def go():
    stations = stations_by_proximity(44, -79)
    print('found', len(stations))

    for station in stations:
        station_dates(station[0])
        # temp_data, precip_data = get_data(station)


if __name__ == '__main__':
    go()
    print('done')
