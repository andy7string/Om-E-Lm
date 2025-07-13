# Copyright 2019 XAMES3. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# ======================================================================
"""
The `pyxa.core.location` module helps with the location related queries.
"""
# The following comment should be removed at some point in the future.
# pylint: disable=import-error
# pylint: disable=no-name-in-module

import os
import random
from datetime import datetime
from typing import AnyStr, List, Optional, Tuple, Union

import geocoder
import googlemaps

from pyxa.constants import DARK, DAWN, DUSK, NOON

def get_coordinates(api_key: AnyStr,
                    location: Optional[str] = None,
                    zone: Optional[str] = None) -> Tuple[str,
                                                         str,
                                                         Union[None, str]]:
    """Gets coordinates and zone for particular location.

    Fetches current or the address location's latitude and longitude
    using reverse lookup via`` Google Maps`` API.

    Args:
        api_key: Google Maps API key.
        location: Location to be converted to latitude & longitude.
                  Default: None
        zone: Name of the zone. For example: city, country, state etc.
              Default: None

    Example:
        >>> import os
        >>> from pyxa.core.location import get_coordinates
        >>> print(get_coordinates(os.environ.get('MAPS_API_KEY'),
                                  'Fenchurch St, London',
                                  'country'))
        (51.5119243, -0.0808231, 'United Kingdom')

    Returns:
        Tuple of latitude, longitude and the zone.

    Note:
        It uses ``Google Maps`` for retreiving latitude & longitude
        using it's API. Hence it is necessary to generate the API key
        first before running this function.
        You can generate it here: https://console.developers.google.com

    Raises:
        ValueError: If the function is called without a valid API key.
    """
    client = googlemaps.Client(key=api_key, timeout=10)

    if location:
        address = client.geocode(location)
        latitude, longitude = (address[0]['geometry']['location']['lat'],
                               address[0]['geometry']['location']['lng'])
    else:
        current = client.geolocate()
        latitude, longitude = (current['location']['lat'],
                               current['location']['lng'])

    zone = get_zone_name(latitude, longitude, zone)

    return latitude, longitude, zone


def get_zone_name(latitude: float,
                  longitude: float,
                  zone: Optional[str] = None) -> Union[None, str]:
    """Returns ``zone`` for particular location."""
    zone_obj = geocoder.osm([latitude, longitude], method='reverse')

    zone_list = ['street', 'road', 'neighbourhood', 'suburb', 'city', 'town',
                 'suburb', 'state', 'region', 'country']

    if zone:
        return zone_obj.json[zone]
    else:
        for idx in zone_list:
            if zone_obj.json.get(idx, None) is not None:
                return zone_obj.json[idx]


def get_part_of_day() -> str:
    """Returns the part of the day."""
    hour = datetime.now().hour

    if hour >= DAWN and hour < NOON:
        part_of_day = random.choice(['morning', 'day'])
    elif hour >= NOON and hour < DUSK:
        part_of_day = random.choice(['afternoon', 'day'])
    elif hour >= DUSK and hour < DARK:
        part_of_day = 'evening'
    else:
        part_of_day = 'night'

    return part_of_day


def calculate_distance(api_key: str,
                       destination: str,
                       origin: Optional[str] = None,
                       mode: Optional[str] = 'walking',
                       metric: Optional[bool] = True) -> Tuple:
    """Calculates the distance between two places.

    Calulates and returns the distance between two places and the time
    required to cover that distance using chosen mode of travelling.

    Args:
        api_key: Google Maps API key.
        destination: Destination location.
        origin: Origin location. If no origin is passed it'll pick
                current location as ``origin`` location.
                Default: None
        mode: Mode of covering the distance.
              Default: walking [Available: driving, walking, bicycling,
                                           transit]

    Example:
        >>> import os
        >>> from pyxa.core.location import calculate_distance
        >>> print(calculate_distance(os.environ.get('MAPS_API_KEY'), 'London'))
        ('8,731 km', '71 days 23 hours')

    Returns:
        Tuple of distance and time.

    Raises:
        ValueError: If the function is called without a valid API key.
    """
    client = googlemaps.Client(key=api_key, timeout=10)

    if origin is None:
        origin_lat, origin_lng, _ = get_coordinates(api_key)
    else:
        origin_lat, origin_lng, _ = get_coordinates(api_key, location=origin)

    origin_coords = (origin_lat, origin_lng)

    dest_lat, dest_lng, _ = get_coordinates(api_key, destination)
    dest_coords = (dest_lat, dest_lng)

    units = 'metric' if metric else 'imperial'

    dist_obj = client.distance_matrix(origin_coords, dest_coords,
                                      mode=mode, units=units)

    distance = dist_obj['rows'][0]['elements'][0]['distance']['text']
    time = dist_obj['rows'][0]['elements'][0]['duration']['text']

    return distance, time
