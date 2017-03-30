#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Explore the content of DICOM files or dirs.
"""

# ======================================================================
# :: Future Imports
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

# ======================================================================
# :: Python Standard Library Imports
import os  # Miscellaneous operating system interfaces
import sys  # System-specific parameters and functions
import platform  # Access to underlying platform’s identifying data
import datetime  # Basic date and time types
import collections  # High-performance container datatypes
import argparse  # Parser for command-line options, arguments and subcommands
import multiprocessing  # Process-based parallelism
import json  # JSON encoder and decoder [JSON: JavaScript Object Notation]
import warnings  # Warning control

# Python interface to Tcl/Tk
try:
    import tkinter as tk
    import tkinter.ttk as ttk
    import tkinter.messagebox as messagebox
    import tkinter.filedialog as filedialog
    import tkinter.simpledialog as simpledialog
except ImportError:
    import Tkinter as tk
    import ttk
    import tkMessageBox as messagebox
    import tkFileDialog as filedialog
    import tkSimpleDialog as simpledialog

import dcmpi.utils as utl
from dcmpi import INFO, DIRS
from dcmpi import VERB_LVL, D_VERB_LVL, VERB_LVL_NAMES
from dcmpi import msg, dbg

# ======================================================================
# :: determine initial configuration
try:
    import appdirs

    _app_dirs = appdirs.AppDirs(INFO['name'], INFO['author'])
    PATHS = {
        'usr_cfg': _app_dirs.user_config_dir,
        'sys_cfg': _app_dirs.site_config_dir,
    }
except ImportError:
    PATHS = {
        'usr_cfg': os.path.realpath('.'),
        'sys_cfg': os.path.dirname(__file__),
    }

CFG_FILENAME = os.path.splitext(os.path.basename(__file__))[0] + '.cfg.json'
CFG_DIRPATHS = (
    PATHS['usr_cfg'],
    os.path.realpath('.'),
    os.getenv('HOME'),
    os.path.dirname(__file__),
    PATHS['sys_cfg'])


# ======================================================================
def dcmpi_explorer_gui(*args, **kwargs):
    try:
        root = tk.Tk()
        # app = Main(root, args)
        root.mainloop()
    except:
        warnings.warn(
            'Failed to use Graphical UI (GUI).'
            ' Fallback to Text UI (TUI)...')
        dcmpi_explorer_tui(**kwargs)


# ======================================================================
def dcmpi_explorer_tui(*args, **kwargs):
    try:
        import asciimatics
    except ImportError:
        asciimatics = None
    # check if asciimatics is available
    if not asciimatics:
        warnings.warn(
            'Package not found: `asciimatics`.')
        warnings.warn(
            'Failed to use Text UI (TUI).'
            ' Fallback to command-line interface (CLI)...')
        dcmpi_explorer_cli(**kwargs)
    else:
        pass


# ======================================================================
def dcmpi_explorer_cli(*args, **kwargs):
    msg('We-are-doomed...')
    pass


# ======================================================================
def handle_arg():
    """
    Handle command-line application arguments.
    """
    # :: Create Argument Parser
    arg_parser = argparse.ArgumentParser(
        description=__doc__,
        epilog='v.{} - {}\n{}'.format(
            INFO['version'], INFO['author'], INFO['license']),
        formatter_class=argparse.RawDescriptionHelpFormatter)
    # :: Add POSIX standard arguments
    arg_parser.add_argument(
        '--ver', '--version',
        version='%(prog)s - ver. {}\n{}\n{} {}\n{}'.format(
            INFO['version'],
            next(line for line in __doc__.splitlines() if line),
            INFO['copyright'], INFO['author'], INFO['notice']),
        action='version')
    arg_parser.add_argument(
        '-v', '--verbose',
        action='count', default=D_VERB_LVL,
        help='increase the level of verbosity [%(default)s]')
    # :: Add additional arguments
    arg_parser.add_argument(
        'ui_mode',
        nargs='?',
        default='tui',
        help='set UI mode [%(default)s]')
    arg_parser.add_argument(
        '-f', '--force',
        action='store_true',
        help='force new processing [%(default)s]')
    arg_parser.add_argument(
        '-c', '--config', metavar='FILE',
        default=CFG_FILENAME,
        help='set configuration file name/path [%(default)s]')
    return arg_parser


# ======================================================================
def main(ui_mode=None):
    """
    Main entry point for the script.
    """
    # :: handle program parameters
    arg_parser = handle_arg()
    args = arg_parser.parse_args()
    # :: print debug info
    if args.verbose >= VERB_LVL['debug']:
        arg_parser.print_help()
        msg('\nARGS: ' + str(vars(args)), args.verbose, VERB_LVL['debug'])
    msg(__doc__.strip())
    begin_time = datetime.datetime.now()

    if not ui_mode:
        ui_mode = args.ui_mode

    if utl.has_graphics(ui_mode):
        dcmpi_explorer_gui()
    elif utl.has_term(ui_mode):
        dcmpi_explorer_tui()
    else:
        dcmpi_explorer_cli()

    exec_time = datetime.datetime.now() - begin_time
    msg('ExecTime: {}'.format(exec_time), args.verbose, VERB_LVL['debug'])


# ======================================================================
if __name__ == '__main__':
    main()
