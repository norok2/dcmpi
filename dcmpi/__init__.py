#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DCMPI: DICOM Preprocessing Interface
"""


# Copyright (C) 2015 Riccardo Metere <metere@cbs.mpg.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


# ======================================================================
# :: Future Imports
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals


# ======================================================================
# :: Versioning
__version__ = "$Revision$"
# $Source$


# ======================================================================
# :: Project Details
INFO = {
    'authors': (
        'Riccardo Metere <metere@cbs.mpg.de>',
        ),
    'copyright': 'Copyright (C) 2015',
    'license': 'License: GNU General Public License version 3 (GPLv3)',
    'notice':
        """
This program is free software and it comes with ABSOLUTELY NO WARRANTY.
It is covered by the GNU General Public License version 3 (GPLv3).
You are welcome to redistribute it under its terms and conditions.
        """,
    'version': __version__
    }


# ======================================================================
# :: supported verbosity levels (level 4 skipped on purpose)
VERB_LVL = {'none': 0, 'low': 1, 'medium': 2, 'high': 3, 'debug': 5}
D_VERB_LVL = VERB_LVL['low']


# ======================================================================
# Greetings
MY_GREETINGS = """
 ____   ____ __  __ ____ ___
|  _ \ / ___|  \/  |  _ \_ _|
| | | | |   | |\/| | |_) | |
| |_| | |___| |  | |  __/| |
|____/ \____|_|  |_|_|  |___|

"""
# generated with: figlet 'DCMPI' -f standard
# note: '\' characters need to be escaped (with another '\')

# :: Causes the greetings to be printed any time the library is loaded.
print(MY_GREETINGS)
