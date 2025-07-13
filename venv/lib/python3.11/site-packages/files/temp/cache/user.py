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
The `pyxa.utils.user` module provides utility for capturing user data.
"""
# The following comment should be removed at some point in the future.
# pylint: disable=import-error
# pylint: disable=no-name-in-module

import os
import random

from questionary import text
from yaml import load, Loader

from pyxa.utils.settings import (CACHE_PATH, DEF_ACTION_PORT, DEF_AI,
                                 DEF_NAME, DEF_SOCKET_PORT, DEF_USERNAME,
                                 DEFAULT_CHARSET, USER_PROFILE_PATH)
from pyxa.utils.template import template


def navigate_to_file(path: str) -> None:
    """Navigates to the user file.

    Checks if the path to the file is valid and navigates to the user
    profile, ``profile.yml`` file in the project directory.

    Arg:
        path: Path of the project directory.

    Raises:
        FileNotFoundError: If the file could not be found in the path.
        NotADirectoryError: If path provided by the user is invalid.
    """
    if os.path.exists(path):
        if os.path.exists(os.path.join(path, USER_PROFILE_PATH)):
            temp = os.path.join(os.path.join(path, CACHE_PATH), 'profile_tmp')
            if os.path.isfile(temp):
                with open(temp, 'r') as tmp:
                    status = tmp.readline().split('\n')[0]
                    status = 'Errorneous' if status == '' else status
                    print(f'{status} profile detected.')
            else:
                raise FileNotFoundError('Could not find necessary files.')
        else:
            raise FileNotFoundError('Profile not found. Please ensure the '
                                    'path to the project is correct.')
    else:
        raise NotADirectoryError(f'The provided path "{path}" doesn\'t exist.')


def add_details_to_file(path: str) -> None:
    """Adds configuration details.

    Adds the user configuration details to the config file. These
    configurations can be modifed later/manually and are stored in
    project directory as a ``.yml`` file.

    Arg:
        path: Path of the project directory.

    Example:
        >>> from pyxa.utils.user import add_details_to_file
        >>> add_details_to_file("Z:/pyxa/tests/charlotte/")
         Enter name (default: XA MES3): XA MES3
         Enter username (default: XA): XA
         ...
         ...
         Enter DarkSky API key: <darksky key>
        Saving all details to the profile file. You can change them ...
    """
    name = f'Enter name (default: {DEF_NAME}):'
    username = f'Enter username (default: {DEF_USERNAME}):'
    ai_name = f'Enter Natural Language AI name (default: {DEF_AI}):'
    action = f'Action server port (default: {DEF_ACTION_PORT}):'
    socket = f'SocketIO Url port (default: {DEF_SOCKET_PORT}):'
    gcp = 'Enter Google Cloud API key:'
    dky = 'Enter DarkSky API key:'

    name = text(name, default=DEF_NAME, qmark='').ask()
    username = text(username, default=DEF_USERNAME, qmark='').ask()
    ai_name = text(ai_name, default=DEF_AI, qmark='').ask()
    action = text(action, default=str(DEF_ACTION_PORT), qmark='').ask()
    socket = text(socket, default=str(DEF_SOCKET_PORT), qmark='').ask()
    gcp = text(gcp, qmark='').ask()
    dky = text(dky, qmark='').ask()

    status = 'Updated' if all([name, username, ai_name,
                               gcp, dky, action, socket]) else 'Incomplete'

    print('Saving all details to the profile file. You can change them later.')

    details = template.render(user_id=random.randint(0000000000, 9999999999),
                              user_name=str(name).capitalize(),
                              user_addressing_name=str(username).capitalize(),
                              assistant_name=str(ai_name).capitalize(),
                              action_server_port=int(action),
                              socketio_port=int(socket),
                              google_cloud_platform_api_key=gcp,
                              darksky_api_key=dky)

    temp = os.path.join(os.path.join(path, CACHE_PATH), 'profile_tmp')
    path = os.path.join(path, USER_PROFILE_PATH)

    with open(path, 'w', encoding=DEFAULT_CHARSET) as file:
        file.write(details)
        with open(temp, 'w', encoding=DEFAULT_CHARSET) as tmp:
            tmp.write(f'{status}')


def update_details_in_file(path: str) -> None:
    """Updates configuration details.

    Checks if the user config file exists and updates the configuration
    details.

    Arg:
        path: Path of the project directory.
    """
    if os.path.exists(path):
        temp = os.path.join(os.path.join(path, CACHE_PATH), 'profile_tmp')
        path = os.path.join(path, USER_PROFILE_PATH)

        file = load(open(path), Loader=Loader)
        id = file['user']['id']
        old_name = file['user']['name']
        old_username = file['user']['address_as']
        old_ai_name = file['ai']['name']
        old_action = file['port']['action_server']
        old_socket = file['port']['socketio']
        old_gcp = file['key']['google_cloud']
        old_dky = file['key']['darksky']

        name = f'Update name (current: {old_name}):'
        username = f'Update username (current: {old_username}):'
        ai_name = f'Update Natural Language AI name (current: {old_ai_name}):'
        action = f'Update Action server port (current: {old_action}):'
        socket = f'Update SocketIO Url port (current: {old_socket}):'
        gcp = f'Update Google Cloud API key (current: {old_gcp}):'
        dky = f'Update DarkSky API key (current: {old_dky}):'

        name = text(name, default=old_name, qmark='').ask()
        username = text(username, default=old_username, qmark='').ask()
        ai_name = text(ai_name, default=old_ai_name, qmark='').ask()
        action = text(action, default=str(old_action), qmark='').ask()
        socket = text(socket, default=str(old_socket), qmark='').ask()
        gcp = text(gcp, default=old_gcp, qmark='').ask()
        dky = text(dky, default=old_dky, qmark='').ask()

        status = 'Modified' if all([name, username, ai_name, gcp,
                                    dky, action, socket]) else 'Incomplete'

        print('Saving updated details to the profile file. You can change '
              'them later.')

        details = template.render(user_id=id,
                                  user_name=str(name).capitalize(),
                                  user_addressing_name=str(
                                      username).capitalize(),
                                  assistant_name=str(ai_name).capitalize(),
                                  action_server_port=int(action),
                                  socketio_port=int(socket),
                                  google_cloud_platform_api_key=gcp,
                                  darksky_api_key=dky)

        temp = os.path.join(os.path.join(path, CACHE_PATH), 'profile_tmp')
        path = os.path.join(path, USER_PROFILE_PATH)

        with open(path, 'w', encoding=DEFAULT_CHARSET) as file:
            file.write(details)
            with open(temp, 'w', encoding=DEFAULT_CHARSET) as tmp:
                tmp.write(f'{status}')
    else:
        raise NotADirectoryError(f'The provided path "{path}" doesn\'t exist.')


# print(type(update_details_in_file('Z:/pyxa/tests/charlotte')))
