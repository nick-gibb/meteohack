from flask import render_template, flash, redirect, url_for, jsonify, request
from app import app
from app.forms import LoginForm
import requests
import pandas as pd
import geopy.distance
from passwords import GOOGLE_KEY

filename = "data/010_room_air_conditioners_climatiseurs_individuels/010_Data_Données.csv"
acs = pd.read_csv(filename, encoding='cp1252')

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

print('hyi')
print(GOOGLE_KEY)
r = requests.get(
    "https://geo.weather.gc.ca/geomet/features/collections/climate-monthly/items")
j = r.json()

stations = []
station_names = []
for feature in j['features']:
    props = feature['properties']

    station = {
        "STATION_NAME": props['STATION_NAME'],
        "LONGITUDE": props['LONGITUDE'],
        "LATITUDE": props['LATITUDE'],
        "COOLING_DEGREE_DAYS": props['COOLING_DEGREE_DAYS']
    }
    if props['COOLING_DEGREE_DAYS'] is not None:
        if props['STATION_NAME'] not in station_names:
            stations.append(station)
            station_names.append(props['STATION_NAME'])
stations_df = pd.DataFrame(stations)
stations_df_reduced = stations_df[stations_df['COOLING_DEGREE_DAYS'] != 0.0]

records_dict = pd.read_csv('data/records_df.csv').T.to_dict()


def get_nearest_design_temp(coordinates):
    nearest_station_distance = None
    nearest_station = None
    for station in records_dict.values():

        lat = float(station['lat'])
        long = float(station['long'])
        station_coord = (lat, long)
        distance = geopy.distance.distance(coordinates, station_coord).km

        if nearest_station_distance == None:
            nearest_station_distance = distance
            nearest_station = station
        else:
            if distance < nearest_station_distance:
                nearest_station_distance = distance
                nearest_station = station
    return nearest_station


# def cooling_days_at_nearest_station(coordinates):
#     nearest_station_distance = None
#     COOLING_DEGREE_DAYS = None
#     name_nearest_station = None
#     for index, row in stations_df.iterrows():
#         lat = float(row['LATITUDE'])
#         long = float(row['LONGITUDE'])
#         weather_station_coord = (lat, long)

#         distance = geopy.distance.distance(
#             coordinates, weather_station_coord).km

#         if index == 0:
#             nearest_station_distance = distance
#             COOLING_DEGREE_DAYS = row['COOLING_DEGREE_DAYS']
#             name_nearest_station = row['STATION_NAME']
#         else:
#             if distance < nearest_station_distance:
#                 nearest_station_distance = distance
#                 COOLING_DEGREE_DAYS = row['COOLING_DEGREE_DAYS']
#                 name_nearest_station = row['STATION_NAME']

#     return COOLING_DEGREE_DAYS


def get_air_con_info(brand, model):
    air_con_info = acs[(acs["BRAND_NAME"] == "Wallmate") & (
        acs["MODEL_NUM_1"] == "SCA09LS")]
    air_con_info_needed = {
        "EE_RATIO": air_con_info['EE_RATIO'].values.tolist()[0],
        "COOL_CAP_BTU": air_con_info['COOL_CAP_BTU'].values.tolist()[0]
    }
    return air_con_info_needed


def get_postal_info(postal):
    url_postal = "https://maps.googleapis.com/maps/api/geocode/json?address={postal}&key={key}".format(
        postal=postal, key=GOOGLE_KEY)
    print(url_postal)
    r = requests.get(url_postal)
    print(r.status_code)
    if r.status_code == 200:
        return r.json()
    else:
        return "Invalid postal code"


def get_energy_rate(province):
    energy_rate = ENERGY_RATES[province]
    return str(energy_rate)


def cooling_days_at_nearest_station(coordinates):
    nearest_station_distance = None
    COOLING_DEGREE_DAYS = None
    name_nearest_station = None
    for index, row in stations_df_reduced.iterrows():
        lat = float(row['LATITUDE'])
        long = float(row['LONGITUDE'])
        weather_station_coord = (lat, long)

        distance = geopy.distance.distance(
            coordinates, weather_station_coord).km
        print(distance)
        print("index", index)
        if nearest_station_distance is None:
            nearest_station_distance = distance
            COOLING_DEGREE_DAYS = row['COOLING_DEGREE_DAYS']
            name_nearest_station = row['STATION_NAME']
        else:
            if distance < nearest_station_distance:
                nearest_station_distance = distance
                COOLING_DEGREE_DAYS = row['COOLING_DEGREE_DAYS']
                name_nearest_station = row['STATION_NAME']
    # print("name_nearest_station", name_nearest_station)
    # print("nearest_station_distance", nearest_station_distance)
    # print("COOLING_DEGREE_DAYS", COOLING_DEGREE_DAYS)

    return COOLING_DEGREE_DAYS, name_nearest_station, nearest_station_distance


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/get_models')
def get_models():
    brand_requested = request.args.get("brand")
    models = acs[acs["BRAND_NAME"] ==
                 brand_requested]['MODEL_NUM_1'].unique().tolist()
    return jsonify(models)


@app.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST':
        # print(request.form)
        postal_info = get_postal_info(form.postal.data)
        postal_code_2 = postal_info['results'][0]['address_components'][0]['long_name']
        neighborhood = postal_info['results'][0]['address_components'][1]['long_name']
        city = postal_info['results'][0]['address_components'][2]['long_name']
        postal_location = postal_info['results'][0]['geometry']['location']
        postal_centroid = (postal_location["lat"], postal_location["lng"])

        cooling_days, name_nearest_station, nearest_station_distance = cooling_days_at_nearest_station(
            postal_centroid)
        nearest_station = get_nearest_design_temp(postal_centroid)
        design_temp_F = nearest_station['design_temp']
        # Convert to celcius
        design_temp = round((design_temp_F - 32) * 5/9, 1)
        province = postal_info['results'][0]['address_components'][4]['short_name']
        energy_rate = float(get_energy_rate(province))
        model = form.model.data
        brand = form.brand.data

        air_con_info = get_air_con_info(brand, model)
        COOL_CAP_BTU = air_con_info["COOL_CAP_BTU"]
        EE_RATIO = air_con_info["EE_RATIO"]

        # cooling_days = 359

        operation_cost = 24 * (cooling_days / (design_temp - 18)) * \
            (COOL_CAP_BTU / (EE_RATIO*.9)) * (energy_rate/1000)

        # print("operation_cost", operation_cost)
        return render_template('results.html', name_nearest_station=name_nearest_station.capitalize(), nearest_station_distance=int(nearest_station_distance), brand=brand, model=model, postal_info=postal_info, energy_rate=energy_rate, province=province, EE_RATIO=EE_RATIO, COOL_CAP_BTU=COOL_CAP_BTU, postal_centroid=postal_centroid, cooling_days=cooling_days, design_temp=design_temp, operation_cost=int(operation_cost), postal_code_2=postal_code_2, neighborhood=neighborhood, city=city)
    else:
        return render_template('submit_postal.html',  title='Energy use', form=form)
