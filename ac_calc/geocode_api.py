import logging
from typing import Union
from dataclasses import dataclass
import googlemaps
from passwords import GOOGLE_KEY

logger = logging.getLogger(__name__)


# singleton
_GMAPS_CLIENT = None


def get_gmaps_client():
    global _GMAPS_CLIENT

    if not _GMAPS_CLIENT:
        _GMAPS_CLIENT = googlemaps.Client(GOOGLE_KEY)

    return _GMAPS_CLIENT


DUMMY_RESULT = [
    {
        'address_components': [
            {'long_name': 'M5G 1P7', 'short_name': 'M5G 1P7', 'types': ['postal_code']},
            {'long_name': 'Old Toronto', 'short_name': 'Old Toronto', 'types': ['political', 'sublocality', 'sublocality_level_1']},
            {'long_name': 'Toronto', 'short_name': 'Toronto', 'types': ['locality', 'political']},
            {'long_name': 'Toronto Division', 'short_name': 'Toronto Division', 'types': ['administrative_area_level_2', 'political']},
            {'long_name': 'Ontario', 'short_name': 'ON', 'types': ['administrative_area_level_1', 'political']},
            {'long_name': 'Canada', 'short_name': 'CA', 'types': ['country', 'political']}
        ],
        'formatted_address': 'Toronto, ON M5G 1P7, Canada',
        'geometry': {
            'bounds': {
                'northeast': {'lat': 43.65510279999999, 'lng': -79.3836815},
                'southwest': {'lat': 43.6546518, 'lng': -79.3850315}
            },
            'location': {
                'lat': 43.6549375,
                'lng': -79.3844795
            },
            'location_type': 'APPROXIMATE',
            'viewport': {
                'northeast': {'lat': 43.6562262802915, 'lng': -79.3830075197085},
                'southwest': {'lat': 43.6535283197085, 'lng': -79.3857054802915}
            }
        },
        'place_id': 'ChIJS3l968s0K4gR8csmsfb6F2o',
        'types': ['postal_code']
    }
]


@dataclass()
class GeoData:
    lat: float
    long: float
    prov_code: str
    province: str
    city: str
    neighbourhood: str
    postal_code: str


# TODO: cache to avoid hitting the API
def get_geo_data(address: str) -> Union[GeoData, None]:
    gmaps = get_gmaps_client()

    geocode_result = gmaps.geocode(address)
    # geocode_result = DUMMY_RESULT

    # print(geocode_result)

    if not geocode_result:
        logger.warning('No geocode results returned')
        return

    if len(geocode_result) != 1:
        logger.warning('Multiple geocode results returned, picking first')

    geocode = geocode_result[0]

    formatted_address = geocode['formatted_address']
    logger.debug(f'Geocoded: {formatted_address}')

    address_components = geocode['address_components']

    prov_info = get_from_address_components(address_components, 'administrative_area_level_1')
    prov_code = prov_info['short_name']
    province = prov_info['long_name']

    city_info = get_from_address_components(address_components, 'locality')
    city = city_info['long_name']

    neighbourhood_info = get_from_address_components(address_components, 'sublocality')
    neighbourhood = neighbourhood_info['long_name'] if neighbourhood_info else None

    postal_info = get_from_address_components(address_components, 'postal_code')
    postal_code = postal_info['long_name']

    location = geocode['geometry']['location']

    return GeoData(location['lat'], location['lng'], prov_code, province, city, neighbourhood, postal_code)


def get_from_address_components(address_components, type_name):
    component = list(filter(lambda a: type_name in a['types'], address_components))

    if not component:
        logger.warning(f'no components found for {type_name}')
        return

    return component[0]
