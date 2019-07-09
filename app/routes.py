from flask import render_template, flash, redirect, url_for
from app import app
from app.forms import LoginForm
import requests

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


@app.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # flash('Login requested for user {}'.format(form.postal.data))
        province = get_province(form.postal.data)
        energy_rate = get_energy_rate(province)
        print(province)
        print(energy_rate)
        return render_template('results.html', energy_rate=energy_rate, province=province)
    return render_template('submit_postal.html',  title='Energy use', form=form)
