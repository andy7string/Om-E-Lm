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
The `pyxa.cli.arguments` module allows passing arguments to a command.

These arguments often begin with ``-`` or ``--``.

All the arguments added in this module should begin with the keyword
``pass`` and end with the keyword ``arg`` seperated with underscores
between them.

For example:
    * pyxa create project --name <these come here>
    * pyxa create project --name <these come here> --path <and here>
"""
# The following comment should be removed at some point in the future.
# pylint: disable=import-error
# pylint: disable=no-name-in-module

import argparse
import logging
from typing import Optional, Union

from pyxa.utils.settings import AI_NAME, VENV_NAME

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def pass_project_name_arg(parser: Union[argparse.ArgumentParser,
                                        argparse._ActionsContainer],
						  help: str,
                          default: Optional[str] = AI_NAME.lower()) -> None:
    """Passes argument for the project name."""
    parser.add_argument('--name', default=default,
                        help=help, type=str, metavar='<name>')


def pass_project_path_arg(parser: Union[argparse.ArgumentParser,
                                        argparse._ActionsContainer],
                          help: str,
                          default: Optional[str] = 'current directory'
                          ) -> None:
    """Passes argument for the project path."""
    parser.add_argument('--path', default=default,
                        help=help, type=str, metavar='<path>')


def pass_venv_name_arg(parser: Union[argparse.ArgumentParser,
                                     argparse._ActionsContainer],
                       help: str,
                       default: Optional[str] = VENV_NAME) -> None:
    """Passes argument for name of the virtual environment."""
    parser.add_argument('--venv', default=default,
                        help=help, type=str, metavar='<name>')


def add_logging_options(parser: Union[argparse.ArgumentParser,
                                      argparse._ActionsContainer]) -> None:
    """Adds logging options to the parser object."""
    parser = parser.add_argument_group('Logging Options')
    parser.add_argument('-v',
                        '--verbose',
                        action='store_const',
                        dest='loglevel',
                        help='Give more output. Increase output verbosity.',
                        const=logging.INFO)
    parser.add_argument('-d',
                        '--debug',
                        action='store_const',
                        dest='loglevel',
                        help='Print all debugging statements.',
                        const=logging.DEBUG)
    parser.add_argument('-q',
                        '--quiet',
                        action='store_const',
                        dest='loglevel',
                        help=('Give less output. Decrease output verbosity '
                              '(respond only to WARNING, ERROR, and '
                              'CRITICAL logging levels).'),
                        const=logging.WARNING)
