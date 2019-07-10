from typing import List
import re
from flask import render_template, flash, redirect, url_for, jsonify, request
from app import app
from app.forms import LoginForm

from ac_calc.geocode_api import get_geo_data
from ac_calc.data import get_models_for_brand, get_location_cdd, get_energy_rate, get_ac_values, \
    get_design_temp_and_station, get_operation_cost

print('hyi')


def parse_years(year_string: str) -> List[int]:
    return [int(y) for y in re.findall(r'(\d{4})', year_string)]


def get_climate_model_name(model_name: str) -> str:
    if model_name == '26':
        return 'RCP2.6'

    if model_name == '45':
        return 'RCP4.5'

    if model_name == '85':
        return 'RCP8.5'


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/get_models')
def get_models():
    brand_requested = request.args.get("brand")
    models = get_models_for_brand(brand_requested)
    return jsonify(models)


@app.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST':
        # print(request.form)

        geo_data = get_geo_data(form.postal.data)

        address_coords = (geo_data.lat, geo_data.long)

        design_temp_station, design_temp_dist, design_temp = get_design_temp_and_station(address_coords)

        energy_rate = get_energy_rate(geo_data.prov_code)

        model = form.model.data
        brand = form.brand.data

        cooling_cap_btu, ee_ratio = get_ac_values(brand, model)

        years = parse_years(form.years.data)

        yearly_op_cost = {}
        yearly_cdd = {}

        for year in years:
            climate_model_ccd = {}
            climate_model_cost = {}

            for climate_model in ['26', '45', '85']:
                cdd = get_location_cdd(geo_data.lat, geo_data.long, year, climate_model)

                climate_model_display_name = get_climate_model_name(climate_model)

                operation_cost = get_operation_cost(cdd, design_temp, cooling_cap_btu, ee_ratio, energy_rate)

                climate_model_ccd[climate_model_display_name] = cdd
                climate_model_cost[climate_model_display_name] = round(operation_cost, 2)

            yearly_cdd[year] = climate_model_ccd
            yearly_op_cost[year] = climate_model_cost

        # print("operation_cost", operation_cost)
        return render_template('results.html', yearly_op_cost=yearly_op_cost, yearly_cdd=yearly_cdd,
                               name_nearest_station=design_temp_station.station.capitalize(),
                               nearest_station_distance=int(design_temp_dist), brand=brand, model=model,
                               energy_rate=energy_rate, province=geo_data.province, EE_RATIO=ee_ratio, COOL_CAP_BTU=cooling_cap_btu,
                               postal_centroid=address_coords, design_temp=design_temp, postal_code_2=geo_data.postal_code,
                               neighborhood=geo_data.neighbourhood, years=years,
                               city=geo_data.city)
    else:
        return render_template('submit_postal.html', title='Energy use', form=form)
