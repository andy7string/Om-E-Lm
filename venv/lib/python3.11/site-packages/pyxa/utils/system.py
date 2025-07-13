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
The `pyxa.utils.system` module provides functions specific to Windows.

These functions provide an utility for handling Windows system related
events.

Note:
    These functions work and are tested on Windows 10 and should* work
    on older versions of Windows as well.
"""
# The following comment should be removed at some point in the future.
# pylint: disable=import-error
# pylint: disable=no-name-in-module

# This is for the Win32con and Win32Gui import
# pyright: reportMissingImports=false

import cProfile
import ctypes
import io
import os
import pstats
import random
import time
from datetime import date, datetime
from itertools import cycle, islice
from typing import Any, Callable, List, Optional, Union

import requests

from pyxa.utils.common import find_string
from pyxa.utils.settings import DEFAULT_PING_URL


def profiler(function: Callable) -> Any:
    """Profiler & optimizer decorator.

    Decorator function that uses cProfile to profile, test & optimise
    other functions. The profiling is done at the later stage once the
    bruteforced code is compliled.

    Returns:
        ``inner`` function object which displays the stats of the
        operating function.
    """

    def inner(*args: Any, **kwargs: Any) -> None:
        """Inner decorator function."""
        profile = cProfile.Profile()
        profile.enable()
        ret_val = function(*args, **kwargs)
        profile.disable()
        string = io.StringIO()
        sort_by = 'cumulative'
        stats = pstats.Stats(profile,stream=string).sort_stats(sort_by)
        stats.print_stats(10)
        print(string.getvalue())
        return ret_val
    return inner


def active_windows() -> List:
    """Returns list of active windows"""
    # You can find the reference code here:
    # https://sjohannes.wordpress.com/2012/03/23/win32-python-getting-all-window-titles/
    EnumWindowsProc = ctypes.CFUNCTYPE(ctypes.c_bool,
                                       ctypes.POINTER(ctypes.c_int),
                                       ctypes.POINTER(ctypes.c_int))
    titles = []

    def _each_window(hwnd: str, lParam: str) -> bool:
        """Function which pulls boolean status of each active window."""
        if ctypes.cdll.user32.IsWindowVisible(hwnd):
            length = ctypes.cdll.user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            ctypes.cdll.user32.GetWindowTextW(hwnd, buff, length + 1)
            titles.append(buff.value)
        return True

    # Listing all active windows, includes windows with no title too.
    ctypes.cdll.user32.EnumWindows(EnumWindowsProc(_each_window), 0)
    # Returns list of only active windows with title names.
    return list(filter(None, titles))


def minimize_window(window_title: str, delay: Union[float, int] = 1.0) -> None:
    """Minimizes window."""
    # You can find the reference code here:
    # https://stackoverflow.com/questions/25466795/how-to-minimize-a-specific-window-in-python?noredirect=1&lq=1
    from win32con import SW_MINIMIZE
    from win32gui import FindWindow, ShowWindow

    time.sleep(delay) if delay else time.sleep(1.0)
    # Minimizes window using the find_string's fuzzy logic.
    ShowWindow(FindWindow(None, find_string(window_title, active_windows())),
               SW_MINIMIZE)


def check_internet(timeout: Optional[Union[float, int]] = 10.0) -> bool:
    """Checks the internet."""
    # You can find the reference code here:
    # https://gist.github.com/yasinkuyu/aa505c1f4bbb4016281d7167b8fa2fc2
    try:
        _ = requests.get(DEFAULT_PING_URL, timeout=timeout)
        return True
    except ConnectionError:
        return False


def find_file(file: str,
              directory: str,
              min_score: Optional[int] = 70) -> Optional[str]:
    """Finds file in the directory.

    Finds the file in the directory using fuzzy logic.

    Args:
        file: Approximate or Exact file name to search in the directory.
        directory: Directory in which the file needs to be searched in.
        min_score: Minimum score needed to make an approximate guess.
                   Default: 70

    Example:
        from pyxa.utils.system import find_file
        >>> print(find_file('Okami', 'D:/Music/'))
        Okami - Kamiki Village.mp3

    Returns:
        file name to be searched from the directory.

    Raises:
        FileNotFoundError: If file not found.
    """
    from fuzzywuzzy.fuzz import partial_ratio
    from fuzzywuzzy.process import extract

    # This will give us list of 3 best matches for our search query.
    guessed = extract(file,
                      os.listdir(directory),
                      limit=3,
                      scorer=partial_ratio)

    for best_guess in guessed:
        current_score = partial_ratio(file, best_guess)
        if current_score > min_score and current_score > 0:
            return best_guess[0]
        else:
            raise FileNotFoundError('File not found.')


def resolve_days(days: Optional[int] = None) -> Union[int, str]:
    """Returns day."""
    week = ['monday',
            'tuesday',
            'wednesday',
            'thursday',
            'friday',
            'saturday',
            'sunday']

    today = datetime.now()

    if days == 0 or days is None:
        return 'today'
    elif days == 1:
        return 'tomorrow'
    elif days == 2:
        idx = date.weekday(today) + 2
        return random.choice(['day after tomorrow', week[idx]])
    elif days > 2 and days < 7:
        idx = date.weekday(today) + days
        # You can find the reference code here:
        # https://stackoverflow.com/a/27594943
        return list(islice(cycle(week), idx, idx + 1))[0]
    else:
        return days
