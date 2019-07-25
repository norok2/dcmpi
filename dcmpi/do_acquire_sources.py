#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Extract DICOM files from a directory.

Move (or copy) DICOM files from the input directory onto the output directory,
for later processing. Assume all DICOM files are from the same session.
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
from dcmpi import util
from dcmpi import INFO, PATH
from dcmpi import VERB_LVL, D_VERB_LVL, VERB_LVL_NAMES
from dcmpi import msg, dbg, fmt, fmtm


# ======================================================================
def do_acquire_sources(
        in_dirpath,
        out_dirpath,
        method='symlink',
        subpath='{study}/{name}_{date}_{time}_{sys}',
        extra_subpath=util.ID['dicom'],
        force=False,
        verbose=D_VERB_LVL):
    """
    Get all DICOM within an input directory.

    Args:
        in_dirpath (str): Path to input directory.
        out_dirpath (str): Path to output directory.
        method (str): DICOM sources fetch method.
            Available options are:
             - 'copy': Copy files from source to destination
             - 'move': Move files from source to destination (use with care!)
             - 'symlink': Create a symbolic link (must be supported by OS)
        subpath (str): Extra subpath to append to output dirpath.
            Extract and interpret fields from DICOM, according to field
            specifications: <field::format>.
            For more info on the accepted syntax, see
            `utils.fill_from_dicom()`.
        extra_subpath (str):
        force (bool): Force new processing.
        verbose (int): Set level of verbosity.

    Returns:
        dcm_dirpaths : str set
        Paths to directories containing DICOM files separated by session.

    See Also:
        utils.fill_from_dicom,
        utils.find_a_dicom
    """

    def get_filepaths(dirpath):
        for root, dirs, files in os.walk(in_dirpath):  # no need to sort
            for name in files:
                yield os.path.join(root, name)

    msg(':: Importing sources...')
    msg('Input:  {}'.format(in_dirpath))
    msg('Output: {}'.format(out_dirpath))

    method = method.lower()

    if method == 'move':
        msg('W: Files will be moved!', fmtt='{t.yellow}{t.bold}')
    elif method == 'symlink':
        msg('W: Files will be linked!', fmtt='{t.yellow}{t.bold}')
    if os.path.exists(in_dirpath):
        # :: analyze directory tree
        dcm_dirpaths = set()
        for filepath in get_filepaths(in_dirpath):
            msg('Analyzing `{}`...'.format(filepath),
                verbose, VERB_LVL['debug'])
            filename = os.path.basename(filepath)
            is_dicom = util.is_dicom(
                filepath,
                allow_dir=False,
                allow_report=True,
                allow_postprocess=True)
            if not is_dicom:
                is_compressed, compression = util.is_compressed_dicom(
                    filepath,
                    allow_dir=False,
                    allow_report=True,
                    allow_postprocess=True)
            else:
                is_compressed = False
                compression = None
            if is_dicom or is_compressed and compression in util.COMPRESSIONS:
                dcm_subpath = None
                if subpath or extra_subpath:
                    full_subpath = os.path.join(subpath, extra_subpath)
                elif subpath:
                    full_subpath = subpath
                else:  # if extra_subpath:
                    full_subpath = extra_subpath
                if full_subpath:
                    dcm_subpath = util.fill_from_dicom(full_subpath, filepath)
                    dcm_dirpath = os.path.join(out_dirpath, dcm_subpath)
                else:
                    dcm_dirpath = out_dirpath
                if not os.path.exists(dcm_dirpath):
                    os.makedirs(dcm_dirpath)
                if dcm_dirpath not in dcm_dirpaths:
                    if dcm_subpath:
                        msg('Subpath: {}'.format(dcm_subpath),
                            verbose, VERB_LVL['low'])
                    dcm_dirpaths.add(dcm_dirpath)
                fake_path = os.path.dirname(os.path.relpath(
                    filepath, in_dirpath)).replace(
                    os.path.sep, util.INFO_SEP) + util.INFO_SEP
                out_filepath = os.path.join(dcm_dirpath, fake_path + filename)
                if not os.path.isfile(out_filepath) or force:
                    if method == 'move':
                        shutil.move(filepath, out_filepath)
                    elif method == 'copy':
                        shutil.copy(filepath, out_filepath)
                    elif method == 'symlink':
                        os.symlink(filepath, out_filepath)
                    elif method == 'link':
                        os.link(filepath, out_filepath)
                else:
                    msg('I: Skipping existing output path. '
                        'Use `force` to override.')
            else:
                name = filepath[len(in_dirpath):]
                msg('W: Invalid source found `{}`'.format(name),
                    verbose, VERB_LVL['medium'])
    else:
        dcm_dirpaths = None
        msg('W: Input path does NOT exists.', verbose, VERB_LVL['low'])
    return dcm_dirpaths


# ======================================================================
def handle_arg():
    """
    Handle command-line application arguments.
    """
    # :: Create Argument Parser
    arg_parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=fmtm('v.{version} - {author}\n{license}', INFO),
        formatter_class=argparse.RawDescriptionHelpFormatter)
    # :: Add POSIX standard arguments
    arg_parser.add_argument(
        '--ver', '--version',
        version=fmt(
            '%(prog)s - ver. {version}\n{}\n{copyright} {author}\n{notice}',
            next(line for line in __doc__.splitlines() if line), **INFO),
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
        '-m', '--method', metavar='copy|move|symlink|link',
        default='symlink',
        help='Move DICOM sources instead of copying [%(default)s]')
    arg_parser.add_argument(
        '-s', '--subpath',
        default='{study}/{name}_{date}_{time}_{sys}',
        help='Append DICOM-generated subpath to output [%(default)s]')
    arg_parser.add_argument(
        '-e', '--extra_subpath',
        default='dcm',
        help='Append static subpath to output [%(default)s]')
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
    do_acquire_sources(**kws)

    exec_time = datetime.datetime.now() - begin_time
    msg('ExecTime: {}'.format(exec_time), args.verbose, VERB_LVL['debug'])


# ======================================================================
if __name__ == '__main__':
    main()
