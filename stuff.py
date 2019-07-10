from ac_calc.geocode_api import get_geo_data
from ac_calc.data import get_location_cdd, get_ac_values, get_energy_rate, \
    get_design_temp_and_station, get_operation_cost

from app.routes import parse_years


def go():
    geo_data = get_geo_data('M5G 1P7')
    print(geo_data)

    address_coords = (geo_data.lat, geo_data.long)

    design_temp_station, design_temp_dist, design_temp = get_design_temp_and_station(address_coords)
    print(f'design temp station: {design_temp_station.station}, {design_temp_dist}, {design_temp}')

    energy_rate = get_energy_rate(geo_data.prov_code)
    print(f'energy rate: {energy_rate} cents / kWh')

    cooling_cap_btu, ee_ratio = get_ac_values('Uberhaus', 'MWK-15CRN1-BK2')
    print(f'cooling cap: {cooling_cap_btu} btu, ee: {ee_ratio}')

    yearly_op_cost = {}

    for y in [1958, 1984, 2019, 2096]:
        climate_model_cost = {}

        for model in ['26', '45', '85']:
            print(f'{model}, {y}')

            cdd = get_location_cdd(geo_data.lat, geo_data.long, y, model)
            print(f'-CDD: {cdd}')

            operation_cost = get_operation_cost(cdd, design_temp, cooling_cap_btu, ee_ratio, energy_rate)
            print(f'operation cost: {operation_cost}')

            climate_model_cost[model] = operation_cost

        yearly_op_cost[y] = climate_model_cost


if __name__ == '__main__':
    go()
