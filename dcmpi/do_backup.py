#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Safely do_backup DICOM files for later use. This is part of DCMPI.

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
# import pydicom as pydcm  # PyDicom (Read, modify and write DICOM files.)

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
from dcmpi import INFO  # , DIRS
from dcmpi import VERB_LVL, D_VERB_LVL, VERB_LVL_NAMES
from dcmpi import msg, dbg

# ======================================================================
ARCHIVE_EXT = {
    'tlz': 'tar.lz',
    'tgz': 'tar.gz',
    'tbz2': 'tar.gz',
    '7z': '7z',
    'zip': 'zip',
    'txz': 'tar.xz',
}


# ======================================================================
def do_backup(
        in_dirpath,
        out_dirpath=None,
        name='{name}_{date}_{time}_{sys}',
        method='7z',
        keep=False,
        force=False,
        verbose=D_VERB_LVL):
    """
    Safely do_backup DICOM files and test the produced archive.

    Args:
        in_dirpath (str): Path to input directory.
        out_dirpath (str): Path to output directory.
        name (str): The name of the backup file.
            Extract and interpret fields from DICOM, according to field
            specifications: <field::format>.
            For more information on accepted syntax,
            see `utl.fill_from_dicom()`.
        method (str): The Compression method.
            Accepted values:
             - '7z': Use 7z compression format.
        keep (bool): Do NOT remove DICOM sources afterward.
        force (bool): Force new processing.
        verbose (int): Set level of verbosity.

    Returns:
        None.
    """

    def _success(ret_code, p_stdout, p_stderr):
        # and p_stdout.find('Everything is Ok') > 0
        return not ret_code

    msg(':: Backing up DICOM folder...')
    msg('Input:  {}'.format(in_dirpath))
    dcm_filename, compression = utl.find_a_dicom(in_dirpath)
    out_basename = utl.fill_from_dicom(name, dcm_filename)
    if not out_dirpath:
        out_dirpath = os.path.dirname(in_dirpath)
    out_filepath = os.path.join(out_dirpath, out_basename)
    if method in ARCHIVE_EXT:
        out_filepath += '.' + ARCHIVE_EXT[method]
    msg('Output: {}'.format(out_filepath))
    success = False
    if not os.path.exists(out_filepath) or force:
        if method == 'tlz':
            cmd_token_list = [
                'tar', '--lzip', '-cf', out_filepath, in_dirpath]
            cmd = ' '.join(cmd_token_list)
            ret_code, p_stdout, p_stderr = utl.execute(cmd, verbose=verbose)
            success = len(p_stderr) == 0
            msg(':: Backup was' + (' ' if success else ' NOT ') + 'sucessful.')
            # :: test archive
            cmd_token_list = ['lzip', '-t', out_filepath]
            cmd = ' '.join(cmd_token_list)
            ret_code, p_stdout, p_stderr = utl.execute(cmd, verbose=verbose)
            success = _success(ret_code, p_stdout, p_stderr)
            msg(':: Test was' + (' ' if success else ' NOT ') + 'sucessful.')

        elif method == 'tgz':
            cmd_token_list = [
                'tar', '--gzip', '-cf', out_filepath, in_dirpath]
            cmd = ' '.join(cmd_token_list)
            ret_code, p_stdout, p_stderr = utl.execute(cmd, verbose=verbose)
            success = len(p_stderr) == 0
            msg(':: Backup was' + (' ' if success else ' NOT ') + 'sucessful.')
            # :: test archive
            cmd_token_list = ['gzip', '-t', out_filepath]
            cmd = ' '.join(cmd_token_list)
            ret_code, p_stdout, p_stderr = utl.execute(cmd, verbose=verbose)
            success = _success(ret_code, p_stdout, p_stderr)
            msg(':: Test was' + (' ' if success else ' NOT ') + 'sucessful.')

        elif method == 'tbz2':
            cmd_token_list = [
                'tar', '--bzip2', '-cf', out_filepath, in_dirpath]
            cmd = ' '.join(cmd_token_list)
            ret_code, p_stdout, p_stderr = utl.execute(cmd, verbose=verbose)
            success = len(p_stderr) == 0
            msg(':: Backup was' + (' ' if success else ' NOT ') + 'sucessful.')
            # :: test archive
            cmd_token_list = ['bzip2', '-t', out_filepath]
            cmd = ' '.join(cmd_token_list)
            ret_code, p_stdout, p_stderr = utl.execute(cmd, verbose=verbose)
            success = _success(ret_code, p_stdout, p_stderr)
            msg(':: Test was' + (' ' if success else ' NOT ') + 'sucessful.')

        elif method == '7z':
            cmd_token_list = [
                '7z', 'a', '-mx9', out_filepath, in_dirpath]
            cmd = ' '.join(cmd_token_list)
            ret_code, p_stdout, p_stderr = utl.execute(cmd, verbose=verbose)
            success = _success(ret_code, p_stdout, p_stderr)
            msg(':: Backup was' + (' ' if success else ' NOT ') + 'sucessful.')
            # :: test archive
            cmd_token_list = ['7z', 't', out_filepath]
            cmd = ' '.join(cmd_token_list)
            ret_code, p_stdout, p_stderr = utl.execute(cmd, verbose=verbose)
            success = _success(ret_code, p_stdout, p_stderr)
            msg(':: Test was' + (' ' if success else ' NOT ') + 'sucessful.')

        elif method == 'zip':
            cmd_token_list = [
                'zip', 'a', '-mx9', out_filepath, in_dirpath]
            cmd = ' '.join(cmd_token_list)
            ret_code, p_stdout, p_stderr = utl.execute(cmd, verbose=verbose)
            success = len(p_stderr) == 0
            msg(':: Backup was' + (' ' if success else ' NOT ') + 'sucessful.')
            # :: test archive
            cmd_token_list = ['zip', '-T', out_filepath]
            cmd = ' '.join(cmd_token_list)
            ret_code, p_stdout, p_stderr = utl.execute(cmd, verbose=verbose)
            success = _success(ret_code, p_stdout, p_stderr)
            msg(':: Test was' + (' ' if success else ' NOT ') + 'sucessful.')

        elif method == 'txz':
            cmd_token_list = [
                'tar', '--xz', '-cf', out_filepath, in_dirpath]
            cmd = ' '.join(cmd_token_list)
            ret_code, p_stdout, p_stderr = utl.execute(cmd, verbose=verbose)
            success = len(p_stderr) == 0
            msg(':: Backup was' + (' ' if success else ' NOT ') + 'sucessful.')
            # :: test archive
            cmd_token_list = ['xz', '-t', out_filepath]
            cmd = ' '.join(cmd_token_list)
            ret_code, p_stdout, p_stderr = utl.execute(cmd, verbose=verbose)
            success = _success(ret_code, p_stdout, p_stderr)
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
    arg_parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='override verbosity settings to suppress output [%(default)s]')
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
        '-n', '--name', metavar='STR',
        default='{name}_{date}_{time}_{sys}',
        help='set output directory [%(default)s]')
    arg_parser.add_argument(
        '-m', '--method', metavar='tlz|tgz|tbz2|7z|zip|txz',
        default='tlz',
        help='set compression method [%(default)s]')
    arg_parser.add_argument(
        '-k', '--keep',
        action='store_true',
        help='Keep DICOM sources after do_backup (and test). [%(default)s]')
    return arg_parser


# ======================================================================
def main():
    """
    Main entry point for the script.
    """
    # :: handle program parameters
    arg_parser = handle_arg()
    args = arg_parser.parse_args()
    # fix verbosity in case of 'quiet'
    if args.quiet:
        args.verbose = VERB_LVL['none']
    # :: print debug info
    if args.verbose >= VERB_LVL['debug']:
        arg_parser.print_help()
        msg('\nARGS: ' + str(vars(args)), args.verbose, VERB_LVL['debug'])
    msg(__doc__.strip())
    begin_time = datetime.datetime.now()

    kws = vars(args)
    kws.pop('quiet')
    do_backup(**kws)

    exec_time = datetime.datetime.now() - begin_time
    msg('ExecTime: {}'.format(exec_time), args.verbose, VERB_LVL['debug'])


# ======================================================================
if __name__ == '__main__':
    main()
