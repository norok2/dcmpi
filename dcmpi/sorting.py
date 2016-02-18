#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sort DICOM files for serie and acquisition (saving results to summary file).

Process DICOM files contained in a base directory and move them to new
subfolders generated from serial number and protocol name.
Additionally, group them according to acquisition and save grouping in the
newly created summary file.
Note: assumes DICOM files to be sorted.
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
import dicom as pydcm  # PyDicom (Read, modify and write DICOM files.)

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
import dcmpi.common as dpc
from dcmpi import INFO
from dcmpi import VERB_LVL
from dcmpi import D_VERB_LVL


# ======================================================================
def sorting(
        dirpath,
        summary=None,
        force=False,
        verbose=D_VERB_LVL):
    """
    Sort DICOM files for serie and acquisition. Save results to summary file.

    Parameters
    ==========
    dirpath : str
        Path where to operate.
    summary : str
        File name or path where to save grouping summary.
    force : boolean (optional)
        Force calculation of output.
    verbose : int (optional)
        Set level of verbosity.

    Returns
    =======
    None.

    See Also
    ========
    dcmlib.group_series, dcmlib.dcm_sources

    """
    # :: group dicom files according to serie number
    if verbose > VERB_LVL['none']:
        print('Sort:\t{}'.format(dirpath))
    dirpath = os.path.realpath(dirpath)
    input_list_dict = {}
    for in_filename in sorted(os.listdir(dirpath)):
        in_filepath = os.path.join(dirpath, in_filename)
        try:
            dcm = pydcm.read_file(in_filepath)
        except IOError:
            if verbose >= VERB_LVL['debug']:
                print('WW: failed processing \'{}\''.format(in_filepath))
        except:
            if verbose > VERB_LVL['low']:
                print('WW: failed processing \'{}\''.format(in_filepath))
        else:
            src_id = dpc.INFO_SEP.join(
                (dpc.PREFIX_ID['series'] + '{:0{size}d}'.format(
                    dcm.SeriesNumber, size=dpc.D_NUM_DIGITS),
                 dcm.SeriesDescription))
            if src_id not in input_list_dict:
                input_list_dict[src_id] = []
            input_list_dict[src_id].append(in_filepath)
    # :: move dicom files to serie number folder
    for src_id, sources in sorted(input_list_dict.items()):
        out_subdirpath = os.path.join(dirpath, src_id)
        if not os.path.exists(out_subdirpath) or force:
            if not os.path.exists(out_subdirpath):
                os.makedirs(out_subdirpath)
            for in_filepath in sources:
                out_filepath = os.path.join(
                    out_subdirpath, os.path.basename(in_filepath))
                shutil.move(in_filepath, out_filepath)
    if summary:
        summary_dirpath = os.path.dirname(summary)
        if summary_dirpath:
            if not os.path.exists(summary_dirpath):
                os.makedirs(os.path.dirname(summary))
        else:
            summary = os.path.join(dirpath, summary)
        dpc.group_series(dirpath, summary, force, verbose)


# ======================================================================
def handle_arg():
    """
    Handle command-line application arguments.
    """
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
        action='count', default=D_VERB_LVL,
        help='increase the level of verbosity [%(default)s]')
    # :: Add additional arguments
    arg_parser.add_argument(
        '-f', '--force',
        action='store_true',
        help='force new processing [%(default)s]')
    arg_parser.add_argument(
        '-s', '--summary',
        default=dpc.D_SUMMARY + '.' + dpc.JSON_EXT,
        help='set expt. summary filepath (empty to skip) [%(default)s]')
    arg_parser.add_argument(
        '-d', '--dirpath', metavar='DIR',
        default='.',
        help='set i/o directory path [%(default)s]')
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

    sorting(args.dirpath, args.summary, args.force, args.verbose)

    end_time = time.time()
    if args.verbose > VERB_LVL['low']:
        print('ExecTime: ', datetime.timedelta(0, end_time - begin_time))


# ======================================================================
if __name__ == '__main__':
    main()
