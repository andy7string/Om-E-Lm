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
The `pyxa.cli.options` module enables optional arguments for commands.

These optional arguments are generally passed after a subparser.

For example:
    * pyxa create <these come here>
    * pyxa create project <these come here>

All the arguments added in this module should begin with the command
name and end with the keyword ``arg`` seperated with underscores between
them.
"""
# The following comment should be removed at some point in the future.
# pylint: disable=import-error
# pylint: disable=no-name-in-module

import argparse

from pyxa.cli.arguments import (pass_project_name_arg,
                                pass_project_path_arg,
                                pass_venv_name_arg)


def create_args(parser: argparse.ArgumentParser):
    """Parses arguments for ``create`` command."""
    pass_project_name_arg(parser, help='Name of the application or project.')
    pass_project_path_arg(parser, help='Path to the project directory.')
    pass_venv_name_arg(parser, help='Name of the virtual environment.')


def create_project_args(parser: argparse.ArgumentParser):
    """Parses arguments for ``create project`` command."""
    pass_project_name_arg(parser, help='Name of the application or project.')
    pass_project_path_arg(parser, help='Path to the project directory.')


def create_venv_args(parser: argparse.ArgumentParser):
    """Parses argument for ``create venv`` command."""
    pass_venv_name_arg(parser, help='Name of the virtual environment.')
    pass_project_path_arg(parser, help='Path to the project directory.')
