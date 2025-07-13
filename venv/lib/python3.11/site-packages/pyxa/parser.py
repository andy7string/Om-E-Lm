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
The `pyxa.parser` module helps exposing the main parser.

The functions in this module allow the usage of the pyXA module over the
CLI. The function, ``global_parser`` allows the use of ``pyxa`` keyword
on the CLI whereas the ``main`` function parses the arguments to the
parser object.

The ``global_parser`` functions also allows to share visual similarities
with the ``pip`` module.

Todo:
    * Add support for handling ``help`` as an argument.
"""
# The following comment should be removed at some point in the future.
# pylint: disable=import-error
# pylint: disable=no-name-in-module

import argparse

from pyxa.cli import strings
from pyxa.cli.arguments import add_logging_options
from pyxa.cli.commands import create
from pyxa.cli.formatter import PyXAHelpFormatter as HelpFormatter
from pyxa.utils.common import check_version, set_log_level
from pyxa.utils.settings import PACKAGE_NAME


def global_parser() -> argparse.ArgumentParser:
    """Creates and returns the main parser for pyxa's CLI.

    It powers the main argument parser for the pyXA module and enables
    sharing a lot of visual similarities with the ``pip`` module.

    Returns:
        ArgumentParser object, which stores all the properties of the
        main argument parser.

    Example:
        >>> from pyxa.parser import global_parser
        >>> global_parser()

        ArgumentParser(prog='pyxa', usage='pyxa <command> [options] ...
    """
    print()

    prog = PACKAGE_NAME.lower()
    usage = f'{prog} <command> [options]'

    parser = argparse.ArgumentParser(prog=prog,
                                     usage=usage,
                                     formatter_class=HelpFormatter,
                                     conflict_handler='resolve',
                                     epilog=strings.epilog,
                                     add_help=False)
    parser._positionals.title = 'Commands'
    parser._optionals.title = 'Extra Options'
    parser.add_argument('-h',
                        '--help',
                        action='store_true',
                        default=argparse.SUPPRESS,
                        help='Show help.')
    parser.add_argument('-V',
                        '--version',
                        action='store_true',
                        default=argparse.SUPPRESS,
                        help='Show installed pyXA version and exit.')

    parent_parser = argparse.ArgumentParser(add_help=False)
    add_logging_options(parent_parser)
    parent_parsers = [parent_parser]

    subparsers = parser.add_subparsers(prog=prog)
    create.subparser(subparsers, parents=parent_parsers)

    return parser


def main() -> None:
    """Primary application entrypoint.

    This function is called at the entrypoint. It means that when the
    user runs this function it will display CLI for the pyXA module.

    Example:
        >>> from pyxa.parser import main
        >>> main()

        Usage:
        pyxa <command> [options]

        Commands:
            create       Create project directory structure for the ...

        Extra Options:
        -h, --help     Show help.
        -V, --version  Show installed pyXA version and exit.

        For specific information about a particular command, run ...
        Read complete documentation at: <https://github.com/xames3/pyxa>

        Copyright 2019 XAMES3. All Rights Reserved.
    """
    parser = global_parser()
    cmd_args = parser.parse_args()

    log_level = cmd_args.loglevel if hasattr(cmd_args, 'loglevel') else None
    set_log_level(log_level)

    if hasattr(cmd_args, 'function'):
        cmd_args.function(cmd_args)
    elif hasattr(cmd_args, 'version'):
        check_version(PACKAGE_NAME.lower())
    else:
        parser.print_help()
        exit(1)
