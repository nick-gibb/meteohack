from flask import render_template, flash, redirect, url_for, jsonify, request
from app import app
from app.forms import LoginForm
import requests
import pandas as pd

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


def get_province(postal):
    url_postal = "https://geocoder.ca/?locate={postal}&geoit=xml&json=1".format(
        postal=postal)
    r = requests.get(url_postal)
    if r.status_code == 200:
        province = r.json()["standard"]["prov"]
        return province
    else:
        return "Invalid postal code"


def get_energy_rate(province):
    energy_rate = ENERGY_RATES_PER_1000_KWH[province]
    return str(energy_rate)


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
        province = get_province(form.postal.data)
        energy_rate = get_energy_rate(province)
        return render_template('results.html', energy_rate=energy_rate, province=province, brand=form.brand.data, model=form.model.data)
    else:
        return render_template('submit_postal.html',  title='Energy use', form=form)
