#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Extract images from DICOM files and store them as NIfTI images.
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
# import shutil  # High-level file operations
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
import dicom2nifti

# :: Local Imports
import dcmpi.utils as utl
from dcmpi import INFO, DIRS
from dcmpi import VERB_LVL, D_VERB_LVL, VERB_LVL_NAMES
from dcmpi import msg, dbg


# ======================================================================
def get_nifti(
        in_dirpath,
        out_dirpath,
        method='dcm2nii',
        compressed=True,
        merged=True,
        force=False,
        verbose=D_VERB_LVL):
    """
    Extract images from DICOM files and store them as NIfTI images.

    Parameters
    ==========
    in_dirpath (str): Path to input directory containing sorted DICOM files.
    out_dirpath (str): Path to output directory where to put NIfTI images.
    method : str (optional)
        | Extraction method. Accepted values:
        * isis: Use Enrico Reimer's ISIS tool.
        * dcm2nii: Use Chris Rorden's dcm2nii tool.
    compressed : boolean (optional)
        Produce compressed images (using GZip).
    merged : boolean (optional)
        Produce merged images (in the 4th dimension, usually time).
    force : boolean (optional)
        Force new processing.
    verbose : int (optional)
        Set level of verbosity.

    Returns
    =======
    None.

    """
    msg(':: Exporting NIfTI images ({})...'.format(method))
    msg('Input:  {}'.format(in_dirpath))
    msg('Output: {}'.format(out_dirpath))
    # proceed only if output is not likely to be there
    if not os.path.exists(out_dirpath) or force:
        # :: create output directory if not exists and extract images
        if not os.path.exists(out_dirpath):
            os.makedirs(out_dirpath)
        sources = utl.dcm_sources(in_dirpath)
        d_ext = '.' + utl.EXT['niz'] if compressed else utl.EXT['nii']

        # :: extract nifti
        if method == 'pydicom':
            for src_id in sorted(sources.keys()):
                in_filepath = os.path.join(in_dirpath, src_id)
            # TODO: implement to avoid dependencies
            msg('W: Pure Python method not implemented.',
                verbose, VERB_LVL['medium'])

        if method == 'isis':
            for src_id in sorted(sources.keys()):
                in_filepath = os.path.join(in_dirpath, src_id)
                out_filepath = os.path.join(out_dirpath, src_id + d_ext)
                cmd = 'isisconv -in {} -out {}'.format(
                    in_filepath, out_filepath)
                ret_val, p_stdout, p_stderr = utl.execute(cmd, verbose=verbose)
                if merged:
                    # TODO: implement volume merging
                    msg('W: (isisconv) merging after not implemented.',
                        verbose, VERB_LVL['medium'])

        elif method == 'dcm2nii':
            for src_id in sorted(sources.keys()):
                in_filepath = os.path.join(in_dirpath, src_id)
                # produce nifti file
                opts = ' -t n'
                opts += ' -p n -i n -f n -d n -e y'  # influences the filename
                opts += ' -4 ' + 'y' if merged else 'n'
                opts += ' -g ' + 'y' if compressed else 'n'
                cmd = 'dcm2nii {} -o {} {}'.format(
                    opts, out_dirpath, in_filepath)
                ret_val, p_stdout, p_stderr = utl.execute(cmd, verbose=verbose)
                term_str = 'GZip...' if compressed else 'Saving '
                lines = p_stdout.split('\n') if p_stdout else ()
                # parse result
                old_names = []
                for line in lines:
                    if term_str in line:
                        old_name = line[line.find(term_str) + len(term_str):]
                        old_names.append(old_name)
                if old_names:
                    msg('Parsed names: ', verbose, VERB_LVL['debug'])
                    msg(''.join([': {}\n'.format(n) for n in old_names]),
                        verbose, VERB_LVL['debug'])
                else:
                    msg('E: Could not locate filename in `dcm2nii`.')
                if len(old_names) == 1:
                    old_filepath = os.path.join(out_dirpath, old_names[0])
                    out_filepath = os.path.join(out_dirpath, src_id + d_ext)
                    msg('NIfTI: {}'.format(out_filepath[len(out_dirpath):]))
                    os.rename(old_filepath, out_filepath)
                else:
                    for num, old_name in enumerate(old_names):
                        old_filepath = os.path.join(out_dirpath, old_name)
                        out_filepath = os.path.join(
                            out_dirpath,
                            src_id + utl.INFO_SEP + str(num + 1) + d_ext)
                        msg('NIfTI: {}'.format(out_filepath[len(out_dirpath):]))
                        os.rename(old_filepath, out_filepath)

        elif method == 'dicom2nifti':
            for src_id in sorted(sources.keys()):
                in_filepath = os.path.join(in_dirpath, src_id)
                out_filepath = os.path.join(out_dirpath, src_id + d_ext)
                dicom2nifti.dicom_series_to_nifti(
                in_filepath, out_filepath, reorient_nifti=True)

        else:
            msg('W: Unknown method `{}`.'.format(method))
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
        default='dicom2nifti',
        help='set extraction method [%(default)s]')
    arg_parser.add_argument(
        '-u', '--uncompressed',
        action='store_true',
        help='compress output NIfTI images [%(default)s]')
    arg_parser.add_argument(
        '-p', '--separated',
        action='store_true',
        help='merge timeline series [%(default)s]')
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

    get_nifti(
        args.in_dirpath, args.out_dirpath,
        args.method, not args.uncompressed, not args.separated,
        args.force, args.verbose)

    exec_time = datetime.datetime.now() - begin_time
    msg('ExecTime: {}'.format(exec_time), args.verbose, VERB_LVL['debug'])


# ======================================================================
if __name__ == '__main__':
    main()
