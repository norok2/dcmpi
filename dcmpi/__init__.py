#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DCMPI - DICOM Preprocessing Interface: explore/distill DICOM data.
"""

# Copyright (c) Riccardo Metere <rick@metere.it>

# ======================================================================
# :: Future Imports
from __future__ import (
    division, absolute_import, print_function, unicode_literals, )

# ======================================================================
# :: Python Standard Library Imports

# ======================================================================
# :: External Imports
# import flyingcircus as fc  # Everything you always wanted to have in Python*
from flyingcircus import msg, dbg, fmt, fmtm, elapsed, report, pkg_paths
from flyingcircus import VERB_LVL, VERB_LVL_NAMES, D_VERB_LVL

# ======================================================================
# :: Version
from dcmpi._version import __version__

# ======================================================================
# :: Project Details
INFO = {
    'name': 'DCMPI',
    'author': 'DCMPI developers',
    'contrib': (
        'Riccardo Metere <rick@metere.it>',
    ),
    'copyright': 'Copyright (C) 2015-2018',
    'license': 'GNU General Public License version 3 or later (GPLv3+)',
    'notice':
        """
This program is free software and it comes with ABSOLUTELY NO WARRANTY.
It is covered by the GNU General Public License version 3 (GPLv3+).
You are welcome to redistribute it under its terms and conditions.
        """,
    'version': __version__
}

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

# ======================================================================
PATH = pkg_paths(__file__, INFO['name'], INFO['author'], INFO['version'])

# ======================================================================
if __name__ == '__main__':
    import doctest  # Test interactive Python examples

    msg(__doc__.strip())
    doctest.testmod()
    msg(report())
