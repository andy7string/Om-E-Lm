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
"""Create project subparser command."""
"""
The `pyxa.cli.commands.create` module creates ``create`` subparser
command.

This command creates the project directory at the provided path with the
given name.
"""
# The following comment should be removed at some point in the future.
# pylint: disable=import-error
# pylint: disable=no-name-in-module

import argparse
import os
import subprocess
from typing import List

from pyxa.cli import strings
from pyxa.cli.formatter import PyXAHelpFormatter as HelpFormatter
from pyxa.cli.options import (create_args,
                              create_project_args,
                              create_venv_args)
from pyxa.utils.settings import PACKAGE_NAME

prog = PACKAGE_NAME.lower()


def subparser(subparsers: argparse._SubParsersAction,
              parents: List[argparse.ArgumentParser]) -> None:
    """Creates subparser object."""
    title = os.path.basename(__file__).split('.')[0].capitalize()

    parser = subparsers.add_parser('create',
                                   usage=strings.create_usage,
                                   help=strings.create_help,
                                   formatter_class=HelpFormatter,
                                   parents=parents,
                                   description=strings.create_description)
    create_args(parser)

    parser._positionals.title = f'{title} Options'
    parser._optionals.title = f'{title} Arguments'

    create = parser.add_subparsers()

    create_project_parser = create.add_parser('project',
                                              usage=strings.project_usage,
                                              help=strings.project_help,
                                              formatter_class=HelpFormatter,
                                              parents=parents,
                                              description=(
                                                  strings.project_description))
    create_project_parser.set_defaults(function=create_project)
    create_project_parser._positionals.title = f'{title} Project Options'
    create_project_parser._optionals.title = f'{title} Project Arguments'

    create_venv_parser = create.add_parser('venv',
                                           usage=strings.venv_usage,
                                           help=strings.venv_help,
                                           formatter_class=HelpFormatter,
                                           parents=parents,
                                           description=(
                                               strings.venv_description))
    create_venv_parser.set_defaults(function=create_venv)
    create_venv_parser._positionals.title = f'{title} Venv Options'
    create_venv_parser._optionals.title = f'{title} Venv Arguments'

    parser.set_defaults(function=create_complete)

    create_project_args(create_project_parser)
    create_venv_args(create_venv_parser)


def create_complete(args: argparse.Namespace,
                    name: str = None,
                    path: str = None,
                    venv: str = None) -> None:
    """Creates complete project structure.

    Args:
        args: Arguments for storing attributes.
        name: Name of the project.
        path: Path where the project needs to be created.
        venv: Name of the virtual environment.
    """
    name = name or args.name
    path = path or args.path
    venv = venv or args.venv

    if path == 'current directory': path = os.getcwd()

    create_project(args, name, path)

    venv = os.path.join(os.path.join(path, name), venv).replace('\\', '/')
    print(f'Creating virtual environment...')
    subprocess.call(f'python -m venv {venv}')


def create_project(args: argparse.Namespace,
                   name: str = None,
                   path: str = None) -> None:
    """Creates project structure.

    Args:
        args: Arguments for storing attributes.
        name: Name of the project.
        path: Path where the project needs to be created.
    """
    from pkg_resources import resource_filename
    from distutils.dir_util import copy_tree

    name = name or args.name
    path = path or args.path

    if path == 'current directory': path = os.getcwd()

    path = os.path.join(path, name).replace('\\', '/')
    copy_tree(resource_filename(__name__, 'project_template'), path)
    print(f'Creating project structure in "{path}"')


def create_venv(args: argparse.Namespace,
                path: str = None,
                venv: str = None) -> None:
    """Creates virtual environment.

    Args:
        args: Arguments for storing attributes.
        path: Path where the virtual environment needs to be created.
        venv: Name of the virtual environment.
    """
    path = path or args.path
    venv = venv or args.venv

    if path == 'current directory': path = os.getcwd()

    venv = os.path.join(path, venv).replace('\\', '/')
    print(f'Creating virtual environment...')
    subprocess.call(f'python -m venv {venv}')
