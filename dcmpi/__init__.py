#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DCMPI: DICOM Preprocessing Interface
"""


# ======================================================================
# :: Future Imports
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals


# ======================================================================
# :: Versioning
__version__ = '0.0.1.2'


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
MY_GREETINGS = r"""
 ____   ____ __  __ ____ ___
|  _ \ / ___|  \/  |  _ \_ _|
| | | | |   | |\/| | |_) | |
| |_| | |___| |  | |  __/| |
|____/ \____|_|  |_|_|  |___|

"""
# generated with: figlet 'DCMPI' -f standard

# :: Causes the greetings to be printed any time the library is loaded.
print(MY_GREETINGS)

print(__version__)
