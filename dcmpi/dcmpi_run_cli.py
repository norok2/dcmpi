#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Extract and preprocess DICOM files.
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
# import pydicom as pydcm  # PyDicom (Read, modify and write DICOM files.)

# :: External Imports Submodules
# import matplotlib.pyplot as plt  # Matplotlib's pyplot: MATLAB-like syntax
# import mayavi.mlab as mlab  # Mayavi's mlab: MATLAB-like syntax
# import scipy.optimize  # SciPy: Optimization Algorithms
# import scipy.integrate  # SciPy: Integrations facilities
# import scipy.constants  # SciPy: Mathematal and Physical Constants
# import scipy.ndimage  # SciPy: ND-image Manipulation

# :: Local Imports
from dcmpi.do_acquire_sources import do_acquire_sources
from dcmpi.do_sorting import sorting
import dcmpi.utils as utl
from dcmpi.get_nifti import get_nifti
from dcmpi.get_info import get_info
from dcmpi.get_prot import get_prot
from dcmpi.get_meta import get_meta
from dcmpi.do_backup import do_backup
from dcmpi.do_report import do_report
from dcmpi import INFO, DIRS
from dcmpi import VERB_LVL, D_VERB_LVL, VERB_LVL_NAMES
from dcmpi import msg, dbg


ACTIONS = {
    get_info: 'ciao',
}
# print(ACTIONS)
#     (get_nifti, ),
#     (get_meta, ),
#     (get_prot, ),
#     (do_report, ),
#     (do_backup, ),
# )

# ======================================================================
def process(
        in_dirpath,
        out_dirpath,
        subpath=utl.TPL['acquire'],
        import_subpath=utl.ID['dicom'],
        niz_subpath=utl.ID['niz'],
        meta_subpath=utl.ID['meta'],
        prot_subpath=utl.ID['prot'],
        info_subpath=utl.ID['info'],
        report_template=utl.TPL['report'],
        backup_template=utl.TPL['backup'],
        force=False,
        verbose=D_VERB_LVL):
    """
    Standard preprocessing of DICOM files.

    Args:
        in_dirpath (str): Path to input directory.
        out_dirpath (str): Path to output directory.
        subpath ():
        niz_subpath ():
        meta_subpath ():
        prot_subpath ():
        info_subpath ():
        report_subpath ():
        backup_subpath ():
        force (bool): Force new processing.
        verbose (int): Set level of verbosity.

    Returns:
        None.
    """
    subdirs = (
        niz_subpath, meta_subpath, prot_subpath, info_subpath, report_template,
        backup_template)
    # import
    dcm_dirpaths = do_acquire_sources(
        in_dirpath, out_dirpath, False, subpath, import_subpath, force, verbose)
    for dcm_dirpath in dcm_dirpaths:
        base_dirpath = os.path.dirname(dcm_dirpath)
        # sort
        sorting(
            dcm_dirpath, utl.D_SUMMARY + '.' + utl.EXT['json'],
            force, verbose)
        # other actions
        # actions = [(a, d) for a, d in zip(utl.D_ACTIONS, subdirs)
        #            if d.strip()]
        # for action, subdir in actions:
        #     i_dirpath = dcm_dirpath if action[0] != 'do_report' else \
        #         os.path.join(base_dirpath, info_subpath)
        #     o_dirpath = os.path.join(base_dirpath, subdir)
        #     if verbose >= VERB_LVL['debug']:
        #         print('I:  input dir: {}'.format(i_dirpath))
        #         print('I: output dir: {}'.format(o_dirpath))
        #     func, params = action
        #     func = globals()[func]
        #     params = [(vars()[par[2:]] if str(par).startswith('::') else par)
        #               for par in params]
        #     if verbose >= VERB_LVL['debug']:
        #         print('DBG: {}'.format(params))
        #     func(*params, force=force, verbose=verbose)


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
        '-s', '--subpath',
        default=utl.TPL['acquire'],
        help='Append DICOM-generated subpath to output [%(default)s]')
    arg_parser.add_argument(
        '-n', '--niz_subpath',
        default=utl.ID['niz'],
        help='Sub-path for NIfTI extraction. Empty to skip [%(default)s]')
    arg_parser.add_argument(
        '-m', '--meta_subpath',
        default=utl.ID['meta'],
        help='Sub-path for META extraction. Empty to skip [%(default)s]')
    arg_parser.add_argument(
        '-p', '--prot_subpath',
        default=utl.ID['prot'],
        help='Sub-path for PROT extraction. Empty to skip [%(default)s]')
    arg_parser.add_argument(
        '-t', '--info_subpath',
        default=utl.ID['info'],
        help='Sub-path for INFO extraction. Empty to skip [%(default)s]')
    arg_parser.add_argument(
        '-r', '--report_subpath',
        default=utl.TPL['report'],
        help='Template for the report filename. Empty to skip [%(default)s]')
    arg_parser.add_argument(
        '-b', '--backup_subpath',
        default=utl.TPL['backup'],
        help='Template for the backup filename. Empty to skip [%(default)s]')
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

    dcmpi_cli(
        args.in_dirpath, args.out_dirpath, args.subpath,
        args.niz_subpath, args.meta_subpath, args.prot_subpath, args.info_subpath,
        args.report_subpath, args.backup_subpath,
        args.force, args.verbose)

    exec_time = datetime.datetime.now() - begin_time
    msg('ExecTime: {}'.format(exec_time), args.verbose, VERB_LVL['debug'])


# ======================================================================
if __name__ == '__main__':
    main()
