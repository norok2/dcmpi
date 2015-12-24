#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Extract and preprocess DICOM files from a single session.
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
# import sys  # System-specific parameters and functions
# import shutil  # High-level file operations
# import platform  # Access to underlying platform’s identifying data
# import math  # Mathematical functions
import time  # Time access and conversions
import datetime  # Basic date and time types
# import re  # Regular expression operations
# import operator  # Standard operators as functions
# import collections  # High-performance container datatypes
import argparse  # Parser for command-line options, arguments and sub-commands
# import itertools  # Functions creating iterators for efficient looping
# import functools  # Higher-order functions and operations on callable objects
# import subprocess  # Subprocess management
# import multiprocessing  # Process-based parallelism
# import csv  # CSV File Reading and Writing [CSV: Comma-Separated Values]

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
from dcmpi.import_sources import import_sources
from dcmpi.sorting import sorting
import dcmpi.common as dcmlib
from dcmpi.get_nifti import get_nifti
from dcmpi.get_info import get_info
from dcmpi.get_prot import get_prot
from dcmpi.get_meta import get_meta
from dcmpi.backup import backup
from dcmpi.report import report
from dcmpi import INFO
from dcmpi import VERB_LVL
from dcmpi import D_VERB_LVL


# ======================================================================
def dcmpi(
        in_dirpath,
        out_dirpath,
        subpath='[study]/[name]_[date]_[time]_[sys]/dcm',
        nii_subdir=dcmlib.ID['nifti'],
        meta_subdir=dcmlib.ID['meta'],
        prot_subdir=dcmlib.ID['prot'],
        info_subdir=dcmlib.ID['info'],
        report_subdir=dcmlib.ID['report'],
        backup_subdir=dcmlib.ID['backup'],
        force=False,
        verbose=D_VERB_LVL):
    """
    Standard preprocessing of DICOM files.
    """
    subdirs = (
        nii_subdir, meta_subdir, prot_subdir, info_subdir, report_subdir,
        backup_subdir)
    # core actions (import and sort)
    dcm_dirpaths = import_sources(
        in_dirpath, out_dirpath, False, subpath, force, verbose)
    for dcm_dirpath in dcm_dirpaths:
        base_dirpath = os.path.dirname(dcm_dirpath)
        sorting(
            dcm_dirpath, dcmlib.D_SUMMARY + '.' + dcmlib.JSON_EXT,
            force, verbose)
        # optional actions
        actions = [(a, d) for a, d in zip(dcmlib.D_ACTIONS, subdirs)
            if d.strip()]
        for action, subdir in actions:
            i_dirpath = dcm_dirpath if action[0] != 'report' else \
                os.path.join(base_dirpath, info_subdir)
            o_dirpath = os.path.join(base_dirpath, subdir)
            if verbose >= VERB_LVL['debug']:
                print('II:  input dir: {}'.format(i_dirpath))
                print('II: output dir: {}'.format(o_dirpath))
            func, params = action
            func = globals()[func]
            params = [(vars()[par[2:]] if str(par).startswith('::') else par)
                for par in params]
            if verbose >= VERB_LVL['debug']:
                print('DBG: {}'.format(params))
            func(*params, force=force, verbose=verbose)


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
    d_output_dir = '/nobackup/isar3/raw_data/siemens/'
    # default subpaths
    d_subpath = '[study]/[name]_[date]_[time]_[sys]/dcm'
    d_nii_subdir = dcmlib.ID['nifti']
    d_meta_subdir = dcmlib.ID['meta']
    d_prot_subdir = dcmlib.ID['prot']
    d_info_subdir = dcmlib.ID['info']
    d_report_subdir = dcmlib.ID['report']
    d_backup_subdir = dcmlib.ID['backup']
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
        '-i', '--input', metavar='INPUT_DIR',
        default=d_input_dir,
        help='set input directory [%(default)s]')
    arg_parser.add_argument(
        '-o', '--output', metavar='OUTPUT_DIR',
        default=d_output_dir,
        help='set output directory [%(default)s]')
    arg_parser.add_argument(
        '-s', '--subpath',
        default=d_subpath,
        help='Append DICOM-generated subpath to output [%(default)s]')
    arg_parser.add_argument(
        '-n', '--nii_subdir',
        default=d_nii_subdir,
        help='Subdir for NIfTI extraction. Empty to skip [%(default)s]')
    arg_parser.add_argument(
        '-m', '--meta_subdir',
        default=d_meta_subdir,
        help='Subdir for META extraction. Empty to skip [%(default)s]')
    arg_parser.add_argument(
        '-p', '--prot_subdir',
        default=d_prot_subdir,
        help='Subdir for PROT extraction. Empty to skip [%(default)s]')
    arg_parser.add_argument(
        '-t', '--info_subdir',
        default=d_info_subdir,
        help='Subdir for INFO extraction. Empty to skip [%(default)s]')
    arg_parser.add_argument(
        '-r', '--report_subdir',
        default=d_report_subdir,
        help='Subdir for report generation. Empty to skip [%(default)s]')
    arg_parser.add_argument(
        '-b', '--backup_subdir',
        default=d_backup_subdir,
        help='Subdir for backup. Empty to skip [%(default)s]')
    return arg_parser


# ======================================================================
if __name__ == '__main__':
    # :: handle program parameters
    ARG_PARSER = handle_arg()
    ARGS = ARG_PARSER.parse_args()
    # :: print debug info
    if ARGS.verbose == VERB_LVL['debug']:
        ARG_PARSER.print_help()
        print()
        print('II:', 'Parsed Arguments:', ARGS)
    print(__doc__)
    begin_time = time.time()

    dcmpi(
        ARGS.input, ARGS.output, ARGS.subpath,
        ARGS.nii_subdir, ARGS.meta_subdir, ARGS.prot_subdir, ARGS.info_subdir,
        ARGS.report_subdir, ARGS.backup_subdir,
        ARGS.force, ARGS.verbose)

    end_time = time.time()
    if ARGS.verbose > VERB_LVL['low']:
        print('ExecTime: ', datetime.timedelta(0, end_time - begin_time))
