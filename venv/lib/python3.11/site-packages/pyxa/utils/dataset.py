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
The `pyxa.utils.dataset` module provides utility for manipulating data.

These functions help to perform tasks that enables the user to cleanup,
fix or modify the training data.
"""
# The following comment should be removed at some point in the future.
# pylint: disable=import-error
# pylint: disable=no-name-in-module

import os
import random
from typing import List

from pyxa.utils.settings import DEFAULT_CHARSET


def sort_lines(file: str) -> None:
    """Sorts lines in file."""
    if os.path.isfile(file):
        with open(file, encoding=DEFAULT_CHARSET) as src_file:
            temp_list = sorted(set(src_file.readlines()))
            with open(file, 'w', encoding=DEFAULT_CHARSET) as src_file:
                for line in temp_list:
                    src_file.write(line)
    else:
        raise FileNotFoundError('File not found.')


def randomize_lines(file: str) -> None:
    """Randomizes lines in file."""
    if os.path.isfile(file):
        with open(file, encoding=DEFAULT_CHARSET) as src_file:
            temp_list = list(set(src_file.readlines()))
            random.shuffle(temp_list)
            with open(file, 'w', encoding=DEFAULT_CHARSET) as src_file:
                for line in temp_list:
                    src_file.write(line)
    else:
        raise FileNotFoundError('File not found.')


def random_replace(file: str, find_words: List, replace_words: List) -> None:
    """Replaces words or phrases randomly.

    Randomly replaces selected words with other words.

    Args:
        file: File from which the words needs to be replaced.
        find_words: List of words to be replaced from the file.
        replace_words: List of words to be replaced with in the file.

    Note:
        Use this to replace the common words/patterns in your dataset.

    Raises:
        FileNotFoundError: If file not found.
    """
    if os.path.isfile(file):
        with open(file, encoding=DEFAULT_CHARSET) as src_file:
            temp_list = src_file.readlines()
            with open(file, 'w', encoding=DEFAULT_CHARSET) as src_file:
                for line in temp_list:
                    if any(word in temp_list[line] for word in find_words):
                        replaced_line = temp_list[line].replace(
                            random.choice(find_words),
                            random.choice(replace_words))
                        src_file.write(replaced_line)
                    else:
                        src_file.write(temp_list[line])
    else:
        raise FileNotFoundError('File not found.')


def random_delete_lines(file: str,
                        lines_to_retain: int = 1000) -> None:
    """Deletes lines randomly.

    Randomly deletes lines from the file.

    Args:
        file: File from which the lines are to be deleted.
        lines_to_retain: Number of lines to keep in the file.
                         Default: 1000

    Note:
        If the number of lines in the file is less than 1000, it'll
        delete 10% of the lines. Use this function for shrinking the
        dataset.

    Raises:
        FileNotFoundError: If file not found.
    """
    if os.path.isfile(file):
        with open(file, encoding=DEFAULT_CHARSET) as src_file:
            temp_list = list(set(src_file.readlines()))
            temp_list = list(filter(lambda x: not x.isspace(), temp_list))
            random.shuffle(temp_list)
            with open(file, 'w', encoding=DEFAULT_CHARSET) as src_file:
                if len(temp_list) < int(lines_to_retain):
                    lines_to_retain = (len(temp_list)
                                          - int(0.1 * len(temp_list)))
                shrunked_list = random.choices(temp_list,
                                               k=int(lines_to_retain))
                for line in shrunked_list:
                    src_file.write(line)

    else:
        raise FileNotFoundError('File not found.')
