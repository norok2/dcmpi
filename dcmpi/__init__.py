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
__version__ = '0.0.1.3.dev29+ngaae811c.d20160819'

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
VERB_LVL_NAMES = (
    'none', 'lowest', 'lower', 'low', 'medium', 'high', 'higher', 'highest',
    'warning', 'debug')
VERB_LVL = {k: v for k, v in zip(VERB_LVL_NAMES, range(len(VERB_LVL_NAMES)))}
D_VERB_LVL = VERB_LVL['lowest']

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
        fmt (str|unicode): Format of the message (if `blessed` supported).
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
        >>> msg(s, fmt='{t.green}')  # if ANSI Terminal, green text
        Hello World!
        >>> msg('   :  a b c', fmt='{t.red}{}')  # if ANSI Terminal, red text
           :  a b c
        >>> msg(' : a b c', fmt='cyan')  # if ANSI Terminal, cyan text
         : a b c
    """
    if verb_lvl >= verb_threshold:
        # if blessed is not present, no coloring
        try:
            import blessed
        except ImportError:
            blessed = None

        if blessed:
            t = blessed.Terminal()
            if not fmt:
                if VERB_LVL['low'] < verb_threshold <= VERB_LVL['medium']:
                    e = t.cyan
                elif VERB_LVL['medium'] < verb_threshold < VERB_LVL['debug']:
                    e = t.magenta
                elif verb_threshold >= VERB_LVL['debug']:
                    e = t.blue
                elif text.startswith('I:'):
                    e = t.green
                elif text.startswith('W:'):
                    e = t.yellow
                elif text.startswith('E:'):
                    e = t.red
                else:
                    e = t.white
                # first non-whitespace word
                txt1 = text.split(None, 1)[0]
                # initial whitespaces
                n = text.find(txt1)
                txt0 = text[:n]
                # rest
                txt2 = text[n + len(txt1):]
                txt_kwargs = {
                    'e1': e + (t.bold if e == t.white else ''),
                    'e2': e + (t.bold if e != t.white else ''),
                    't0': txt0, 't1': txt1, 't2': txt2, 'n': t.normal}
                text = '{t0}{e1}{t1}{n}{e2}{t2}{n}'.format(**txt_kwargs)
            else:
                if 't.' not in fmt:
                    fmt = '{{t.{}}}'.format(fmt)
                if '{}' not in fmt:
                    fmt += '{}'
                text = fmt.format(text, t=t) + t.normal
        print(text, *args, **kwargs)


# ======================================================================
def dbg(name, fmt=None):
    """
    Print content of a variable for debug purposes.

    Args:
        name: The name to be inspected.
        fmt (str|unicode): Format of the message (if `blessed` supported).
            If None, a standard formatting is used.

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
    import inspect

    outer_frame = inspect.getouterframes(inspect.currentframe())[1]
    name_str = outer_frame[4][0][:-1]
    msg(name_str, fmt=fmt, end=': ')
    msg(repr(name), fmt='')
