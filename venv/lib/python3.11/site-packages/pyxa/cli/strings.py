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
The `pyxa.cli.strings` module holds usage, help and descriptions strings
for the parsers & subparsers.
"""

# Parent parser object.
epilog = ('For specific information about a particular command, run "pyxa '
          '<command> -h".\nRead complete documentation at: '
          '<https://github.com/xames3/pyxa>\n\nCopyright 2019 XAMES3. '
          'All Rights Reserved.')

# Create subparser object.
create_usage = ('pyxa create [options] --name <project name> --path <local '
                'project path> ...\n  '
                'pyxa create [options] project --name <project name> ...\n  '
                'pyxa create [options] venv --venv <venv name> ...\n  '
                'pyxa create [options] <no arguments> ...')
create_help = ('Create project directory structure for the given project '
               'name in the current directory or optionally in the given '
               'directory to unpack the necessary dependencies into it. Note '
               'that it will unpack everything in "~/.charlotte/" directory '
               'if no name is specified for the project.')
create_description = ('Description:\n  Getting started for Charlotte:\n\n  '
                      '- Creates your Charlotte AI project structure.\n  '
                      '- Creates virtual environment if necessary.\n\n  '
                      'Although everything is configured at the beginning, '
                      'you can change and update things as per your needs.')

# Create project subparser object.
project_usage = ('pyxa create project --name <project name> --path '
                 '<local project path> ...\n  '
                 'pyxa create project --path <local project path> ...\n  '
                 'pyxa create project <no arguments> ...')
project_help = ('Create project directory structure for the given project '
                'name in the current directory or optionally in the given '
                'directory to unpack the necessary dependencies into it. '
                'Note that it will unpack everything in "~/.charlotte/" '
                'directory if no name is specified for the project.')
project_description = ('Description:\n  Similar to "pyxa create":\n\n  '
                       '- Creates your Charlotte AI project structure.\n\n  '
                       'Although everything is configured at the beginning, '
                       'you can change and update things as per your needs.')

# Create venv subparser object.
venv_usage = ('pyxa create venv --venv <venv name> '
              '--path <path to venv> ...\n  '
              'pyxa create venv --path <path to venv> ...')
venv_help = ('Create virtual environment in the existing project directory. '
             'This virtual environment is created at default '
             'path, "~/.<project directory>/<venv name>/". The '
             'default name for the environment is "venv" but can be '
             'changed by specifying the "--venv" argument.')
venv_description = ('Description:\n  Creates virtual environment:\n\n  '
                    '- Virtual environment will be created in the project '
                    'directory.\n  '
                    '- Default name of the virtual environment is '
                    '"venv". You can override this by specifying '
                    '"--venv" argument.\n\n  '
                    'Virtual environment has access to global site packages '
                    'by default. Currently there isn\'t any option available '
                    'to override it.')
