# Copyright (c) 2010 VMware, Inc. All Rights Reserved.

# This file is part of ATOMac.

# ATOMac is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the Free
# Software Foundation version 2 and no later version.

# ATOMac is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License version 2
# for more details.

# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51 Franklin
# St, Fifth Floor, Boston, MA 02110-1301 USA.

# noinspection PyUnresolvedReferences
from future import standard_library # type: ignore
standard_library.install_aliases()

from . import _a11y
from .AXClasses import NativeUIElement
from .Clipboard import Clipboard
from .Prefs import Prefs
from .version import __version__
import http.client as httplib

# Exceptions
Error = _a11y.Error
ErrorAPIDisabled = _a11y.ErrorAPIDisabled
ErrorInvalidUIElement = _a11y.ErrorInvalidUIElement
ErrorCannotComplete = _a11y.ErrorCannotComplete
ErrorUnsupported = _a11y.ErrorUnsupported
ErrorNotImplemented = _a11y.ErrorNotImplemented

Prefs = Prefs
__version__ = __version__
Clipboard = Clipboard

getAppRefByLocalizedName = NativeUIElement.getAppRefByLocalizedName
terminateAppByBundleId = NativeUIElement.terminateAppByBundleId
launchAppByBundlePath = NativeUIElement.launchAppByBundlePath
setSystemWideTimeout = NativeUIElement.setSystemWideTimeout
getAppRefByBundleId = NativeUIElement.getAppRefByBundleId
launchAppByBundleId = NativeUIElement.launchAppByBundleId
getFrontmostApp = NativeUIElement.getFrontmostApp
getAppRefByPid = NativeUIElement.getAppRefByPid

def getAllApps():
    """
    Returns a list of all running app references.
    TODO: Implement actual app enumeration logic for Om-E-Mac.
    """
    return []  # Replace with actual app enumeration logic

def getAllWindows():
    """
    Returns a list of all windows from all running apps known to Om-E-Mac.
    """
    all_windows = []
    for app in getAllApps():
        try:
            all_windows.extend(app.windows())
        except Exception:
            continue
    return all_windows
