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
The `pyxa.utils.common` module implements the common functions.

These functions are very generic in their operation and can-be/are used
within the project. These functions also provide cross project usage i.e
the functions from this module can be used by other python projects.
"""
# The following comment should be removed at some point in the future.
# pylint: disable=import-error
# pylint: disable=no-name-in-module

import logging
import os
import subprocess
import sys
from typing import List, Optional, Union

from pyxa.utils.settings import DEFAULT_LOG_LEVEL, ENV_LOG_LEVEL_NAME

logger = logging.getLogger(__name__)


def check_version(package_name: str) -> None:
    """Compares current and latest version of the package.

    Compares the installed version versus the latest version of package
    available on ``PyPI`` and returns a favorable response. If a newer
    version is available for download it will recommend upgrading to it.

    Arg:
        package_name: Package name whose version needs to be checked.

    Example:
        >>> from pyxa.utils.common import check_version
        >>> check_version()

        You are using the latest version of pyxa, 0.0.1rc1
    """
    current = str(subprocess.run([sys.executable, '-m', 'pip',
                                  'show', package_name],
                                 capture_output=True, text=True))
    name = current[current.find('Name:') + 5:]
    name = name[:name.find('\\n')].replace(' ', '')

    version = current[current.find('Version:') + 8:]
    version = version[:version.find('\\n')].replace(' ', '')

    latest = str(subprocess.run([sys.executable, '-m', 'pip', 'install',
                                 f'{package_name}==random'], capture_output=True, text=True))
    latest = latest[latest.find('(from versions:') + 15:]
    latest = latest[:latest.find(')')]
    latest = latest.replace(' ', '').split(',')[-1]

    if latest == 'none':
        print(f'Installed {name} version is {version}')
    elif version == latest:
        print(f'You are using the latest version of {name}, {version}')
    else:
        print(f'You are using an older version of {name}, {version}. However '
              f'version, {latest} is available for download. You should '
              f'consider upgrading via "pip install --upgrade {name}" '
              'command.')


def set_log_level(log_level: Union[int, str] = None) -> None:
    """Sets logging level.

    Sets a logging level for the operation if it is not set. The default
    logging level is INFO.

    Arg:
        log_level: Logging level to be set.
    """
    if not log_level:
        log_level = os.environ.get(ENV_LOG_LEVEL_NAME, DEFAULT_LOG_LEVEL)
        log_level = logging.getLevelName(log_level)

    logging.getLogger('pyxa').setLevel(log_level)


def find_string(string: str,
                string_list: List,
                min_score: Optional[int] = 70) -> Optional[str]:
    """Finds string in a list.

    Finds the matching string in the list and works similar to
    ``.find()`` but uses fuzzy logic for guessing text from any valid
    list

    Args:
        string: Approximate or Exact string to find from the list.
        string_list: List in which the string needs to be searched in.
        min_score: Minimum score needed to make an approximate guess.
                   Default: 70

    Returns:
        str value to be searched from the string.

    Raises:
        ValueError: If the string couldn't be found in the passed list.
    """
    from fuzzywuzzy.fuzz import partial_ratio
    from fuzzywuzzy.process import extract

    # This will give us list of 3 best matches for our search query.
    guessed = extract(string, string_list, limit=3, scorer=partial_ratio)

    for best_guess in guessed:
        current_score = partial_ratio(string, best_guess)
        if current_score > min_score and current_score > 0:
            return best_guess[0]
        else:
            raise ValueError(f'Couldn\'t find "{string}" in the given list.')
