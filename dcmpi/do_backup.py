#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Safely get_backup DICOM files for later use. This is part of DCMPI.

Warning: misuse of this program may lead to loss of data.
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
import dcmpi.utils as utl
from dcmpi import INFO
from dcmpi import VERB_LVL, D_VERB_LVL
from dcmpi import msg, dbg

# ======================================================================
ARCHIVE_EXT = {
    '7z': '7z',
    'zip': 'zip',
    'txz': 'tar.xz',
    'gxz': 'tar.gz'}


# ======================================================================
def get_backup(
        in_dirpath,
        out_dirpath='dcm',
        method='7z',
        keep=False,
        force=False,
        verbose=D_VERB_LVL):
    """
    Safely get_backup DICOM files and test the produced archive.

    Args:
        in_dirpath (str|unicode): Path to input directory.
        out_dirpath (str|unicode): Path to output directory.
        method (str|unicode): The Compression method.
            Accepted values:
             - '7z': Use 7z compression format.
        keep (bool): Do NOT remove DICOM sources afterward.
        force (bool): Force new processing.
        verbose (int): Set level of verbosity.

    Returns:
        None.
    """
    msg(':: Backing up DICOM folder...')
    msg('Input:  {}'.format(in_dirpath))
    if method in ARCHIVE_EXT:
        out_dirpath += '.' + ARCHIVE_EXT[method]
    msg('Output: {}'.format(out_dirpath))
    success = False
    if not os.path.exists(out_dirpath) or force:
        if method == '7z':
            cmd_token_list = [
                '7z', 'a', '-mx9', out_dirpath, in_dirpath]
            cmd = ' '.join(cmd_token_list)
            ret_val, p_stdout, p_stderr = utl.execute(cmd, verbose=verbose)
            success = ret_val and p_stdout.find('Everything is Ok') > 0
            msg(':: Backup was' + (' ' if success else ' NOT ') + 'sucessful.')
            # :: test archive
            cmd_token_list = ['7z', 't', out_dirpath]
            cmd = ' '.join(cmd_token_list)
            ret_val, p_stdout, p_stderr = utl.execute(cmd, verbose=verbose)
            success = ret_val and p_stdout.find('Everything is Ok') > 0
            msg(':: Test was' + (' ' if success else ' NOT ') + 'sucessful.')

        elif method == 'zip':
            cmd_token_list = [
                'zip', 'a', '-mx9', out_dirpath, in_dirpath]
            cmd = ' '.join(cmd_token_list)
            ret_val, p_stdout, p_stderr = utl.execute(cmd, verbose=verbose)
            success = len(p_stderr) == 0
            msg(':: Backup was' + (' ' if success else ' NOT ') + 'sucessful.')
            # :: test archive
            cmd_token_list = ['7z', 't', out_dirpath]
            cmd = ' '.join(cmd_token_list)
            ret_val, p_stdout, p_stderr = utl.execute(cmd, verbose=verbose)
            success = ret_val and p_stdout.find('Everything is Ok') > 0
            msg(':: Test was' + (' ' if success else ' NOT ') + 'sucessful.')

        else:
            msg('W: Unknown method `{}`.'.format(method))
        if success and not keep and os.path.exists(in_dirpath):
            msg('Remove: {}'.format(in_dirpath))
            shutil.rmtree(in_dirpath, ignore_errors=True)
    else:
        msg('I: Skipping existing output path. Use `force` to override.')


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
        '-f', '--force',
        action='store_true',
        help='force new processing [%(default)s]')
    arg_parser.add_argument(
        '-i', '--in_dirpath', metavar='DIR',
        default='.',
        help='set input directory [%(default)s]')
    arg_parser.add_argument(
        '-o', '--out_dirpath', metavar='DIR',
        default='.',
        help='set output directory [%(default)s]')
    arg_parser.add_argument(
        '-m', '--method', metavar='METHOD',
        default='7z',
        help='set compression method [%(default)s]')
    arg_parser.add_argument(
        '-k', '--keep',
        action='store_true',
        help='Keep DICOM sources after get_backup (and test). [%(default)s]')
    return arg_parser


# ======================================================================
def main():
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

    get_backup(
        args.in_dirpath, args.out_dirpath,
        args.method, args.keep,
        args.force, args.verbose)

    exec_time = datetime.datetime.now() - begin_time
    msg('ExecTime: {}'.format(exec_time), args.verbose, VERB_LVL['debug'])


# ======================================================================
if __name__ == '__main__':
    main()