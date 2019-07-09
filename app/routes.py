from flask import render_template, flash, redirect, url_for, jsonify, request
from app import app
from app.forms import LoginForm
import requests
import pandas as pd
import geopy.distance

filename = "data/010_room_air_conditioners_climatiseurs_individuels/010_Data_Données.csv"
acs = pd.read_csv(filename, encoding='cp1252')

ENERGY_RATES_PER_1000_KWH = {
    "QC": 100,
    "MN": 126,
    "BC": 160,
    "NB": 182,
    "AB": 201,
    "NL": 169,
    "SK": 232,
    "ON": 186,
    "NS": 230
}

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


def cooling_days_at_nearest_station(coordinates):
    nearest_station_distance = None
    COOLING_DEGREE_DAYS = None
    name_nearest_station = None
    for index, row in stations_df.iterrows():
        lat = float(row['LATITUDE'])
        long = float(row['LONGITUDE'])
        weather_station_coord = (lat, long)

        distance = geopy.distance.distance(
            coordinates, weather_station_coord).km

        if index == 0:
            nearest_station_distance = distance
            COOLING_DEGREE_DAYS = row['COOLING_DEGREE_DAYS']
            name_nearest_station = row['STATION_NAME']
        else:
            if distance < nearest_station_distance:
                nearest_station_distance = distance
                COOLING_DEGREE_DAYS = row['COOLING_DEGREE_DAYS']
                name_nearest_station = row['STATION_NAME']

    return COOLING_DEGREE_DAYS


def get_postal_info(postal):
    url_postal = "https://maps.googleapis.com/maps/api/geocode/json?address={postal}&key=AIzaSyCtMlbzEdOw3_0vWbOCWUG1fHaEVQxGWu0".format(
        postal=postal)
    print(url_postal)
    r = requests.get(url_postal)
    print(r.status_code)
    if r.status_code == 200:
        return r.json()
    else:
        return "Invalid postal code"


def get_energy_rate(province):
    energy_rate = ENERGY_RATES_PER_1000_KWH[province]
    return str(energy_rate)


def cooling_days_at_nearest_station(coordinates):
    nearest_station_distance = None
    COOLING_DEGREE_DAYS = None
    name_nearest_station = None
    for index, row in stations_df.iterrows():
        lat = float(row['LATITUDE'])
        long = float(row['LONGITUDE'])
        weather_station_coord = (lat, long)

        distance = geopy.distance.distance(
            coordinates, weather_station_coord).km

        if index == 0:
            nearest_station_distance = distance
            COOLING_DEGREE_DAYS = row['COOLING_DEGREE_DAYS']
            name_nearest_station = row['STATION_NAME']
        else:
            if distance < nearest_station_distance:
                nearest_station_distance = distance
                COOLING_DEGREE_DAYS = row['COOLING_DEGREE_DAYS']
                name_nearest_station = row['STATION_NAME']
    print("name_nearest_station", name_nearest_station)
    print("nearest_station_distance", nearest_station_distance)
    print("COOLING_DEGREE_DAYS", COOLING_DEGREE_DAYS)

    return COOLING_DEGREE_DAYS


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
        postal_location = postal_info['results'][0]['geometry']['location']
        postal_centroid = (postal_location["lat"], postal_location["lng"])
        print(postal_centroid)
        cooling_days = cooling_days_at_nearest_station(postal_centroid)
        province = postal_info['results'][0]['address_components'][4]['short_name']
        energy_rate = get_energy_rate(province)
        return render_template('results.html', energy_rate=energy_rate, province=province, brand=form.brand.data, model=form.model.data, postal_centroid=postal_centroid, cooling_days=cooling_days)
    else:
        return render_template('submit_postal.html',  title='Energy use', form=form)
