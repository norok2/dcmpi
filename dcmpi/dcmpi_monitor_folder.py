#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Monitor folder for creation of new DICOM folder.
"""

#    Copyright (C) 2015 Riccardo Metere <metere@cbs.mpg.de>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.


# ======================================================================
# :: Future Imports
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

# ======================================================================
# :: Python Standard Library Imports
import os  # Miscellaneous operating system interfaces
# import sys  # System-specific parameters and functions
# import shutil  # High-level file operations
# import platform  # Access to underlying platform’s identifying data
# import locale  # Internationalization services
# import math  # Mathematical functions
import random  # Generate pseudo-random numbers
import time  # Time access and conversions
import datetime  # Basic date and time types
# import re  # Regular expression operations
# import operator  # Standard operators as functions
# import collections  # High-performance container datatypes
import argparse  # Parser for command-line options, arguments and sub-commands
# import itertools  # Functions creating iterators for efficient looping
# import functools  # Higher-order functions and operations on callable objects
import subprocess  # Subprocess management
# import multiprocessing  # Process-based parallelism
# import csv  # CSV File Reading and Writing [CSV: Comma-Separated Values]
# import json  # JSON encoder and decoder [JSON: JavaScript Object Notation]

# :: External Imports
# import numpy as np  # NumPy (multidimensional numerical arrays library)
# import scipy as sp  # SciPy (signal and image processing library)
# import matplotlib as mpl  # Matplotlib (2D/3D plotting library)
# import sympy as sym  # SymPy (symbolic CAS library)
# import PIL  # Python Image Library (image manipulation toolkit)
# import SimpleITK as sitk  # Image ToolKit Wrapper
# import nibabel as nib  # NiBabel (NeuroImaging I/O Library)
# import nipy  # NiPy (NeuroImaging in Python)
# import nipype  # NiPype (NiPy Pipelines and Interfaces)
# import dicom as pydcm  # PyDicom (Read, modify and write DICOM files.)

# :: External Imports Submodules
# import matplotlib.pyplot as plt  # Matplotlib's pyplot: MATLAB-like syntax
# import mayavi.mlab as mlab  # Mayavi's mlab: MATLAB-like syntax
# import scipy.optimize  # SciPy: Optimization Algorithms
# import scipy.integrate  # SciPy: Integrations facilities
# import scipy.constants  # SciPy: Mathematal and Physical Constants
# import scipy.ndimage  # SciPy: ND-image Manipulation

# :: Local Imports
# import mri_tools.modules.base as mrb
# import mri_tools.modules.utils as mru
# import mri_tools.modules.nifti as mrn
# import mri_tools.modules.geometry as mrg
# from mri_tools.modules.sequences import mp2rage
import dcmpi.common as dcmlib
from dcmpi import INFO
from dcmpi import VERB_LVL
from dcmpi import D_VERB_LVL


# ======================================================================
def monitor_folder(
        cmd,
        dirpath,
        delay,
        check,
        on_added=True,
        max_count=0,
        delay_variance=0,
        force=False,
        verbose=D_VERB_LVL):
    """
    Monitor changes in a dir and execute a command upon verify some condition.
    """

    def list_dirs(dirpath):
        return [d for d in os.listdir(dirpath)
                if os.path.isdir(os.path.join(dirpath, d))]

    sec_in_min = 60

    loop = True
    count = 0
    old_dirs = list_dirs(dirpath)
    if verbose > VERB_LVL['none']:
        print('Watch:\t{}'.format(dirpath))
    while loop:
        new_dirs = list_dirs(dirpath)
        removed_dirs = [d for d in old_dirs if d not in new_dirs]
        added_dirs = [d for d in new_dirs if d not in old_dirs]
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S %Z', time.localtime())
        randomized = (random.random() * 2 - 1) * delay_variance \
            if delay_variance else 0
        sleep_delay = (delay + randomized) * sec_in_min
        if verbose > VERB_LVL['none']:
            if removed_dirs:
                msg = '{}  --  {}'.format(timestamp, removed_dirs)
                print(dcmlib.tty_colorify(msg, 'r'))
            if added_dirs:
                msg = '{}  ++  {}'.format(timestamp, added_dirs)
                print(dcmlib.tty_colorify(msg, 'g'))
        if verbose > VERB_LVL['none'] and not removed_dirs and not added_dirs:
            msg = 'All quiet on the western front'
            next_check = time.strftime(
                '%H:%M:%S', time.localtime(time.time() + sleep_delay))
            print('{}      {} (next check in ~{} min, at {})'.format(
                timestamp, msg, int(delay + randomized), next_check))
        delta_dirs = added_dirs if on_added else removed_dirs
        for delta in delta_dirs:
            delta_dirpath = os.path.join(dirpath, delta)
            if check and check(delta_dirpath):
                cmd = cmd.format(delta_dirpath)
                subprocess.call(cmd, shell=True)
                count += 1
        time.sleep(sleep_delay)
        if max_count > 0 and max_count < count:
            loop = False
        else:
            old_dirs = new_dirs
            loop = True


# ======================================================================
def handle_arg():
    """
    Handle command-line application arguments.
    """
    # :: Define DEFAULT values
    # verbosity
    d_verbose = D_VERB_LVL
    # default working directory
    d_dir = '.'
    # default delay in min
    d_delay = 60  # 1 hour
    # default randomized delay variance in min
    d_delay_variance = 5
    # default command
    d_cmd = os.path.dirname(__file__) + '/dcm_analyze_dir.py {}'
    # :: Create Argument Parser
    arg_parser = argparse.ArgumentParser(
        description=__doc__,
        epilog='v.{} - {}\n{}'.format(
            INFO['version'], ', '.join(INFO['authors']), INFO['license']),
        formatter_class=argparse.RawDescriptionHelpFormatter)
    # :: Add POSIX standard arguments
    arg_parser.add_argument(
        '--ver', '--version',
        version='%(prog)s - ver. {}\n{}\n{} {}\n{}'.format(
            INFO['version'],
            next(line for line in __doc__.splitlines() if line),
            INFO['copyright'], ', '.join(INFO['authors']),
            INFO['notice']),
        action='version')
    arg_parser.add_argument(
        '-v', '--verbose',
        action='count', default=d_verbose,
        help='increase the level of verbosity [%(default)s]')
    # :: Add additional arguments
    arg_parser.add_argument(
        '-f', '--force',
        action='store_true',
        help='force new processing [%(default)s]')
    arg_parser.add_argument(
        '-d', '--dir', metavar='DIR',
        default=d_dir,
        help='set working directory [%(default)s]')
    arg_parser.add_argument(
        '-l', '--delay', metavar='VAL',
        type=float, default=d_delay,
        help='set checking interval in min [%(default)s]')
    arg_parser.add_argument(
        '-r', '--delay_var', metavar='VAL',
        type=float, default=d_delay_variance,
        help='set random variance in the delay in min [%(default)s]')
    arg_parser.add_argument(
        '-m', '--max_count', metavar='NUM',
        type=int, default=d_delay,
        help='maximum number of actions to be performed [%(default)s]')
    arg_parser.add_argument(
        '-c', '--cmd', metavar='EXECUTABLE',
        default=d_cmd,
        help='execute when finding a new dir with DICOMs [%(default)s]')
    return arg_parser


# ======================================================================
def main():
    # :: handle program parameters
    arg_parser = handle_arg()
    args = arg_parser.parse_args()
    # :: print debug info
    if args.verbose == VERB_LVL['debug']:
        arg_parser.print_help()
        print()
        print('II:', 'Parsed Arguments:', args)
    print(__doc__)

    begin_time = time.time()

    monitor_folder(
        args.cmd,
        args.dir, args.delay,
        lambda x: dcmlib.find_a_dicom(x)[0],
        True,
        args.max_count, args.delay_var,
        args.force, args.verbose)

    end_time = time.time()
    if args.verbose > VERB_LVL['low']:
        print('ExecTime: ', datetime.timedelta(0, end_time - begin_time))


# ======================================================================
if __name__ == '__main__':
    main()
