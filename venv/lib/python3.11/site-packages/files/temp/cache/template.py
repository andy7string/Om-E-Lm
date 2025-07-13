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
The :mod:`pyxa.utils.template` module provides the boilerplate template
for creating the user profile.
"""

import jinja2

template = jinja2.Template('''# This file contains the user specific details.

# General
# User specific details that the NLA woupip ld use for quick assist.
user:
    id: {{ user_id }}
    name: {{ user_name }}
    address_as: {{ user_addressing_name }}

# Natural Language Assistant
# Character specifications for the NLA.
ai:
    name: {{ assistant_name }}     # [optional] (default: charlotte)

# Security keys
# Keys for making API calls.
key:
    google_cloud: {{ google_cloud_platform_api_key }}
    darksky: {{ darksky_api_key }}
    twilio:     # [optional]

# Ports
# Ports on which the actions & hosting will be performed.
port:
    action_server: {{ action_server_port }}     # [optional] (default: 6969)
    socketio: {{ socketio_port }}     # [optional] (default: 1414)
''')
