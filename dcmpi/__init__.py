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
VERB_LVL = {
    'none': 0, 'low': 1, 'medium': 2, 'high': 3, 'higher': 4, 'highest': 5,
    'debug': 7}
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
        >>> msg(s, fmt='{t.green}')  # if in ANSI Terminal, text is green
        Hello World!
        >>> msg(s, fmt='{t.red}{}')  # if in ANSI Terminal, text is red
        Hello World!
        >>> msg(s, fmt='yellow')  # if in ANSI Terminal, text is yellow
        Hello World!
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
                tokens = text.split(None, 1)
                txt0 = text[:text.find(tokens[0])]
                txt1 = tokens[0]
                txt2 = text[text.find(txt1) + len(txt1)] + tokens[1] \
                    if len(tokens) > 1 else ''
                txt_kwargs = {
                    'e1': e + (t.bold if e == t.white else ''),
                    'e2': e + (t.bold if e != t.white else ''),
                    'init': txt0, 'first': txt1, 'rest': txt2, 'n': t.normal}
                text = '{init}{e1}{first}{n}{e2}{rest}{n}'.format(**txt_kwargs)
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
