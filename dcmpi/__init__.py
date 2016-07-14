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
__version__ = '0.0.1.3.dev15+ng0b85f22.d20160712'

# ======================================================================
# :: Project Details
INFO = {
    'name': 'DCMPI',
    'author': 'Riccardo Metere <metere@cbs.mpg.de>',
    'copyright': 'Copyright (C) 2016',
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


# ======================================================================
def msg(
        text,
        verb_lvl=D_VERB_LVL,
        verb_threshold=D_VERB_LVL,
        fmt=None,
        *args,
        **kwargs):
    """
    Display a feedback message to the standard output.

    Args:
        text (str|unicode): Message to display.
        verb_lvl (int): Current level of verbosity.
        verb_threshold (int): Threshold level of verbosity.
        fmt (str|unicode): Format of the message (if `blessings` supported).
            If None, a standard formatting is used.
        *args (tuple): Positional arguments to be passed to `print`.
        **kwargs (dict): Keyword arguments to be passed to `print`.

    Returns:
        None.

    Examples:
        >>> s = 'Hello World!'
        >>> msg(s)
        Hello World!
        >>> msg(s, VERB_LVL['medium'], VERB_LVL['low'])
        Hello World!
        >>> msg(s, VERB_LVL['low'], VERB_LVL['medium'])  # no output
        >>> msg(s, fmt='{t.green}')  # if in ANSI Terminal, text is green
        Hello World!
        >>> msg(s, fmt='{t.red}{}')  # if in ANSI Terminal, text is red
        Hello World!
    """
    if verb_lvl >= verb_threshold:
        try:
            import blessings
            term = blessings.Terminal()
            if not fmt:
                if verb_lvl == VERB_LVL['medium']:
                    extra = term.cyan
                elif verb_lvl == VERB_LVL['high']:
                    extra = term.yellow
                elif verb_lvl == VERB_LVL['debug']:
                    extra = term.magenta + term.bold
                else:
                    extra = term.white
                text = '{e}{t.bold}{first}{t.normal}{e}{rest}{t.normal}'.format(
                    t=term, e=extra,
                    first=text[:text.find(' ')],
                    rest=text[text.find(' '):])
            else:
                if '{}' not in fmt:
                    fmt += '{}'
                text = fmt.format(text, t=term) + term.normal
        except ImportError:
            pass
        finally:
            print(text, *args, **kwargs)


# ======================================================================
def dbg(name):
    """
    Print content of a variable for debug purposes.

    Args:
        name: The name to be inspected.

    Returns:
        None.

    Examples:
        >>> my_dict = {'a': 1, 'b': 1}
        >>> dbg(my_dict)
        dbg(my_dict): {
            "a": 1,
            "b": 1
        }
        <BLANKLINE>
        >>> dbg(my_dict['a'])
        dbg(my_dict['a']): 1
        <BLANKLINE>
    """
    import json
    import inspect
    outer_frame = inspect.getouterframes(inspect.currentframe())[1]
    name_str = outer_frame[4][0][:-1]
    print(name_str, end=': ')
    print(json.dumps(name, sort_keys=True, indent=4))
    print()
