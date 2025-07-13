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
The `pyxa.core.weather` module helps with the weather forecast.

The functions in this module enables weather forecast related queries
with relative ease.
"""
# The following comment should be removed at some point in the future.
# pylint: disable=import-error
# pylint: disable=no-name-in-module

import os
from typing import Optional, Tuple, Union

import requests

from pyxa.core.location import get_coordinates, get_part_of_day
from pyxa.utils.settings import DEFAULT_WEATHER_URL
from pyxa.utils.system import check_internet, resolve_days


def wind_direction(degree: Union[float, int]) -> str:
    """Returns direction of the wind."""
    directions = ['northern', 'northeastern', 'eastern', 'southeastern',
                  'southern', 'southwestern', 'western', 'northwestern']
    idx = int((degree + 11.25) / 22.5)
    return directions[idx % len(directions)]


def forecast(maps_key: str,
             darksky_key: str,
             location: Optional[str] = None,
             days: Optional[int] = None,
             hours: Optional[int] = None,
             metric: Optional[bool] = True) -> Union[None, Tuple]:
    """Provides weather forecast.

    Fetches the weather forecast for current or particular location on
    basis of days or hours. This is done by making an API call to
    ``DarkSky.net``.

    Args:
        location: Location where to find the weather forecast for.
                  This location can be any valid ``address``.
                  Default: None
        days: Number of days for which the forecast is needed.
              Maximum 7 days forecast is currently possible.
              Default: None
        hours: Number of hours for which the forecast is needed.
               Maximum of 48 hours of forecast is currently possible.
               Default: None
        metric: Metric units to be used, Metric or Imperial.
                Default: True

    Example:
        >>> import os
        >>> from pyxa.core.weather import forecast
        >>> maps_key = os.environ.get('MAPS_API_KEY')
        >>> darksky_key = os.environ.get('DARKSKY_API_KEY')
        >>> print(forecast(maps_key, darksky_key,
                           'London', days=1, metric=True))
        ('London', 0, '2.02°C', '-0.46°C', '12.94°C', '5.33°C', '92.0%',
         '6.24 kph', 'light rain tomorrow through next thursday.',
         'darker', 'southeastern', 'afternoon', 'tomorrow', 'day')

    Returns:
        Tuple object with weather forecast for a location.

    Note:
        An account on ``https://darksky.net/`` is required to get the
        api key. API call is made to retreive the weather report.
        Only 1000 calls can be made per month on the ``free`` tier.

    Raises:
        ValueError: If the function is called without a valid API key.
    """
    if check_internet():
        latitude, longitude, zone = get_coordinates(maps_key, location, 'city')

        if metric:
            units, degree, per_hr = 'si', '°C', 'kph'
        else:
            units, degree, per_hr = 'us', '°F', 'mph'

        url = (f'{DEFAULT_WEATHER_URL}{darksky_key}/{latitude},{longitude}?'
               f'units={units}')
        weather_obj = requests.get(url).json()

        if days and days <= 7 and days > 0:
            data, idx = weather_obj['daily']['data'][days], 0
            temp = f'{weather_obj["currently"]["temperature"]}{degree}'
            feel = f'{weather_obj["currently"]["apparentTemperature"]}{degree}'
            max_temp = f'{data["apparentTemperatureMax"]}{degree}'
            min_temp = f'{data["apparentTemperatureMin"]}{degree}'
        elif hours and hours <= 48:
            data, idx = weather_obj['hourly']['data'][hours], 1
            value = weather_obj['daily']['data'][0]
            temp = f'{data["currently"]["temperature"]}{degree}'
            feel = f'{data["currently"]["apparentTemperature"]}{degree}'
            max_temp = f'{value["apparentTemperatureMax"]}{degree}'
            min_temp = f'{value["apparentTemperatureMin"]}{degree}'
        else:
            data, idx = weather_obj['currently'], 2
            value = weather_obj['daily']['data'][0]
            temp = f'{weather_obj["currently"]["temperature"]}{degree}'
            feel = f'{weather_obj["currently"]["apparentTemperature"]}{degree}'
            max_temp = f'{value["apparentTemperatureMax"]}{degree}'
            min_temp = f'{value["apparentTemperatureMin"]}{degree}'

        condition = f'{(data["summary"]).lower()[:-1]}'

        if condition.startswith('possible'):
            old, new = "possible", "possible to have"
            condition = f'{condition.replace(old, new)} weather'

        if condition.startswith('rain'):
            condition = condition.replace('rain', 'rainy weather')

        if condition.endswith('cloudy'):
            condition = condition + ' weather'

        if condition.startswith('light'):
            old, new = "light", "possible to have light"
            condition = f'{condition.replace(old, new)} weather'

        if condition.startswith('heavy'):
            old, new = "heavy", "possible to have heavy"
            condition = f'{condition.replace(old, new)} weather'

        humidity = f'{data["humidity"] * 100}%'
        speed = f'{data["windSpeed"]} {per_hr}'
        summary = str(weather_obj['daily']['summary']).lower()
        cloud = data['cloudCover']
        sky = 'brighter' if cloud < 0.5 else 'darker'
        direction = wind_direction(data['windBearing'])
        part = get_part_of_day()
        day = resolve_days(days)
        sub = 'day' if days == 1 else 'days'

        return (zone, idx, temp, feel, max_temp, min_temp, humidity, speed,
                summary, sky, direction, part, day, sub)
    else:
        return None
