#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Safely backup DICOM files for later use. This is part of DCMPI.

Warning: misuse of this program may lead to loss of data.
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
import shutil  # High-level file operations
# import math  # Mathematical functions
import time  # Time access and conversions
import datetime  # Basic date and time types
# import operator  # Standard operators as functions
# import collections  # High-performance container datatypes
import argparse  # Parser for command-line options, arguments and sub-commands
# import itertools  # Functions creating iterators for efficient looping
# import functools  # Higher-order functions and operations on callable objects
# import subprocess  # Subprocess management
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
ARCHIVE_EXT = {
    '7z': '7z',
    'zip': 'zip',
    'txz': 'tar.xz',
    'gxz': 'tar.gz',}


# ======================================================================
def backup(
        in_filepath,
        out_filepath='dcm',
        method='7z',
        keep=False,
        force=False,
        verbose=D_VERB_LVL):
    """
    Safely backup DICOM files for later use.

    Parameters
    ==========
    in_dirpath : str
        Path to input directory.
    out_dirpath : str
        Path to output directory.
    method : str (optional)
        | Extraction method. Accepted values:
        * 7z: Use 7z compression format.
    keep : boolean (optional)
        Do NOT remove DICOM sources after backing up (and testing).
    force : boolean (optional)
        Force new processing.
    verbose : int (optional)
        Set level of verbosity.

    Returns
    =======
    None.

    """
    if verbose > VERB_LVL['none']:
        print(':: Backing up DICOM folder...')
    if verbose > VERB_LVL['none']:
        print('Input:\t{}'.format(in_filepath))
    if method in ARCHIVE_EXT:
        out_filepath += '.' + ARCHIVE_EXT[method]
    if verbose > VERB_LVL['none']:
        print('Output:\t{}'.format(out_filepath))
    success = False
    if not os.path.exists(out_filepath) or force:
        if method == '7z':
            # :: perform compression
            cmd_token_list = [
                '7z',
                'a', '-mx9',
                out_filepath,
                in_filepath, ]
            cmd = ' '.join(cmd_token_list)
            p_stdout, p_stderr = dcmlib.execute(cmd, verbose=verbose)
            if verbose >= VERB_LVL['debug']:
                print(p_stdout)
                print(p_stderr)
            success = True if p_stdout.find('Everything is Ok') > 0 else False
            if success and verbose >= VERB_LVL['low']:
                print(':: Backup was successful.')
            # :: test archive
            cmd_token_list = ['7z', 't', out_filepath]
            cmd = ' '.join(cmd_token_list)
            p_stdout, p_stderr = dcmlib.execute(cmd, verbose=verbose)
            if verbose >= VERB_LVL['debug']:
                print(p_stdout)
                print(p_stderr)
            success = True if p_stdout.find('Everything is Ok') > 0 else False
            if success and verbose >= VERB_LVL['low']:
                print(':: Test was successful.')
        else:
            if verbose > VERB_LVL['none']:
                print("WW: Unknown method '{}'.".format(method))
        if success and not keep and os.path.exists(in_filepath):
            if verbose > VERB_LVL['none']:
                print('Remove:\t{}'.format(in_filepath))
            shutil.rmtree(in_filepath, ignore_errors=True)
    else:
        if verbose > VERB_LVL['none']:
            print("II: Output path exists. Skipping. "
                  "Use 'force' argument to override.")


# ======================================================================
def handle_arg():
    """
    Handle command-line application arguments.
    """
    # :: Define DEFAULT values
    # verbosity
    d_verbose = D_VERB_LVL
    # default input directory
    d_input_dir = '.'
    # default output directory
    d_output_dir = '.'
    # default method
    d_method = 'pydicom'
    # :: Create Argument Parser
    arg_parser = argparse.ArgumentParser(
        description=__doc__,
        epilog='v.{} - {}\n{}'.format(
            INFO['version'], ', '.join(INFO['authors']),
            INFO['license']),
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
        '-i', '--input', metavar='DIR',
        default=d_input_dir,
        help='set input directory [%(default)s]')
    arg_parser.add_argument(
        '-o', '--output', metavar='DIR',
        default=d_output_dir,
        help='set output directory [%(default)s]')
    arg_parser.add_argument(
        '-m', '--method', metavar='METHOD',
        default=d_method,
        help='set extraction method [%(default)s]')
    arg_parser.add_argument(
        '-k', '--keep',
        action='store_true',
        help='Keep DICOM sources after backup (and test). [%(default)s]')
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

    backup(
        args.input, args.output,
        args.method, args.keep,
        args.force, args.verbose)

    end_time = time.time()
    if args.verbose > VERB_LVL['low']:
        print('ExecTime: ', datetime.timedelta(0, end_time - begin_time))


# ======================================================================
if __name__ == '__main__':
    main()
