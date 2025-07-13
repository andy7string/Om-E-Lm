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
"""Creates user profile."""

import jinja2
import os
import random
from typing import NoReturn, Text, Union
from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

from questionary import text

from pyxa.utils.exceptions import FileNotFound, PathNotFound
from pyxa.utils.settings import CACHE_PATH, DEFAULT_CHARSET, USER_PROFILE_PATH


template = jinja2.Template('''# This file contains the User specific details.

# General
# User specific details that the NLA would use for quick assist.
user:
    id: {{ user_id }}
    name: {{ user_name }}
    address_as: {{ user_addressing_name }}

# Natural UI
# Character specifications for the NLA.
ai:
    name: {{ assistant_name }}     # [optional] (default: charlotte)

# Security keys
# Keys for making API calls.
key:
    google_cloud: {{ google_cloud_platform_api_key }}
    darksky: {{ darksky_api_key }}

# Ports
# Ports on which the actions & hosting will be performed.
port:
    action_server: {{ action_server_port }}     # [optional] (default: 6969)
    socketio: {{ socketio_port }}     # [optional] (default: 1414)
''')


def navigate_to_file(path: Text) -> Union[NoReturn, Text]:
    """Track user file."""
    if not os.path.exists(path):
        raise PathNotFound
    else:
        print('Project created.')
        if not os.path.exists(os.path.join(path, USER_PROFILE_PATH)):
            raise FileNotFound
        else:
            cache = os.path.join(path, CACHE_PATH)
            if not os.path.isfile(os.path.join(cache, 'profile_tmp')):
                raise FileNotFound('There seems to be a problem with the '
                                   'setup. Couldn\'t find necessary files.')
            else:
                with open(os.path.join(cache, 'profile_tmp'), 'r') as tmp:
                    status = tmp.readline().split('\n')[0]
                    print(f'{status} profile file detected.')


def add_details_to_file(path: Text) -> Union[NoReturn, Text]:
    """Adding config values to file."""
    cache = os.path.join(path, CACHE_PATH)
    print('Before we start setting up the profile, please ensure you '
          'fill all the details.')

    name = str(text('Please enter an username (default: John Wick):',
                    default='John Wick').ask()).capitalize()
    address_as = str(text('How should you be addressed as? (default: John):',
                          default='John').ask()).capitalize()
    ai_name = str(text('Please provide a name to your Natural Language '
                       'Assistant (default: Charlotte):',
                       default='Charlotte').ask()).capitalize()
    gcp = str(text('Your Google Cloud API key:').ask())
    dky = str(text('Your DarkSky API key:').ask())
    action = int(text('Action server port (default: 6969):',
                      default='6969').ask())
    socket = int(text('SocketIO Url port (default: 1414):',
                      default='1414').ask())

    status = 'Updated' if all([name, address_as, ai_name,
                               gcp, dky, action, socket]) else 'Incomplete'

    print('Saving all details to the profile file. You can change them later.')

    details = template.render(user_id=random.randint(0000000000, 9999999999),
                              user_name=name,
                              user_addressing_name=address_as,
                              assistant_name=ai_name,
                              google_cloud_platform_api_key=gcp,
                              darksky_api_key=dky, action_server_port=action,
                              socketio_port=socket)

    path = os.path.join(path, USER_PROFILE_PATH)
    with open(path, 'w', encoding=DEFAULT_CHARSET) as file:
        file.write(details)

    with open(os.path.join(cache, 'profile_tmp'), 'w',
              encoding=DEFAULT_CHARSET) as tmp:
        tmp.write(f'{status}')


def update_details_in_file(path: Text) -> Union[NoReturn, Text]:
    """Updating config values in file."""
    if not os.path.exists(path):
        raise PathNotFound
    else:
        cache = os.path.join(path, CACHE_PATH)
        path = os.path.join(path, USER_PROFILE_PATH)

        print('Loading profile file.')

        file = load(open(path), Loader=Loader)
        id = file['user']['id']
        old_name = file['user']['name']
        old_address_as = file['user']['address_as']
        old_ai_name = file['ai']['name']
        old_action_port = file['port']['action_server']
        old_socket = file['port']['socketio']

        name = str(text(f'Please enter new username (currently: {old_name}):',
                        default=old_name).ask()).capitalize()
        address_as = str(text('How should you be addressed going forward? '
                              f'(currently: {old_address_as}):',
                              default=old_address_as).ask()).capitalize()
        ai_name = str(text('Please provide new name to your Natural Language '
                           f'Assistant (currently: {old_ai_name}):',
                           default=old_ai_name).ask()).capitalize()
        gcp = str(text('Your new Google Cloud API key:').ask())
        dky = str(text('Your new DarkSky API key:').ask())
        action = int(text('New action server port '
                          f'(currently: {old_action_port}):',
                          default=str(old_action_port)).ask())
        socket = int(text(f'New socketIO url port (currently: {old_socket}):',
                          default=str(old_socket)).ask())

        status = 'Modified' if all([name, address_as, ai_name, gcp,
                                    dky, action, socket]) else 'Incomplete'

        print('Saving new details to the profile file. You can change '
              'them later.')

        details = template.render(user_id=id,
                                  user_name=name,
                                  user_addressing_name=address_as,
                                  assistant_name=ai_name,
                                  google_cloud_platform_api_key=gcp,
                                  darksky_api_key=dky,
                                  action_server_port=action,
                                  socketio_port=socket)

        with open(path, 'w', encoding=DEFAULT_CHARSET) as file:
            file.write(details)

        with open(os.path.join(cache, 'profile_tmp'), 'w',
                  encoding=DEFAULT_CHARSET) as tmp:
            tmp.write(f'{status}')
