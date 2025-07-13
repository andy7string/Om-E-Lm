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
The `pyxa.utils.settings` module hosts package constants.

These are pre-defined values to build a composite settings environment,
which can affect and/or update all the depending values at once. These
values should be checked and updated periodically.
"""

# Settings for the package.
PACKAGE_NAME = 'pyxa'
PROJECT_NAME = 'pyXA'
AI_NAME = 'Charlotte'

# This package adheres to Semantic Versioning Specification (SemVer)
# starting with version 0.0.1.
# You can read about it here: https://semver.org/spec/v2.0.0.html
PACKAGE_VERSION = '0.0.2'

# Author details.
AUTHOR = 'XA'
AUTHOR_EMAIL = MAINTAINER_EMAIL = 'xames3.developer@gmail.com'

# Local time zone details.
# You can find all the choices here:
# https://en.wikipedia.org/wiki/List_of_tz_zones_by_name
TIME_ZONE = 'Asia/Kolkata'

# Language used by the project
# You can find all the choices here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-gb'

# Default encoding used for all read-write objects.
DEFAULT_CHARSET = 'utf-8'

# Default urls.
DEFAULT_PING_URL = 'https://www.google.com/'
DEFAULT_WEATHER_URL = 'https://api.darksky.net/forecast/'

# Default package structure.
# You can override this later. pyXA recommends against doing it.
# User config settings.
USER_PATH = 'user'
USER_PROFILE_PATH = USER_PATH + '/profile.yml'

# Cache & garbage collector settings.
FILES_PATH = 'files'
TEMP_PATH = FILES_PATH + '/temp/'
CACHE_PATH = TEMP_PATH + '/cache/'

# Database settings.
DATABASE_PATH = 'database'
DATABASE_FILE_PATH = DATABASE_PATH + '/tracker_store.db'

# Virtual environment settings.
VENV_NAME = 'venv'

# Frontend & UI settings.
FRONTEND_PATH = 'frontend'

# Ports details.
# This port details can be override manually later.
LOCALHOST = 'localhost'
ACTION_SERVER_PORT = 6969
NAUGHTY_HOST_PORT = 1414
TEST_HOST_PORT = 2121

# Logging levels.
# Sets the logging level to INFO.
ENV_LOG_LEVEL_NAME = 'PYXA_LOG_LEVEL'
DEFAULT_LOG_LEVEL = 'INFO'
