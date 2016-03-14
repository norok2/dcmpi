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
import dcmpi.common as dpc
from dcmpi import INFO
from dcmpi import VERB_LVL
from dcmpi import D_VERB_LVL


# ======================================================================
def import_sources(
        in_dirpath,
        out_dirpath,
        clean=False,
        subpath='{study}/{name}_{date}_{time}_{sys}/dcm',
        force=False,
        verbose=D_VERB_LVL):
    """
    Get all DICOM within an input directory.

    Parameters
    ==========
    in_dirpath : str
        Path to input directory.
    out_dirpath : str
        Path to output directory.
    clean : boolean (optional)
        Move DICOM sources instead of copying.
    subpath : str (optional)
        | Extra subpath to append to output dirpath. Interpret fields from
        | DICOM, according to field specifications: <field::format>.
        | See dcmlib.fill_from_dicom for more information on accepted syntax.
    force : boolean (optional)
        Force calculation of output.
    verbose : int (optional)
        Set level of verbosity.

    Returns
    =======
    dcm_dirpaths : str set
        Paths to directories containing DICOM files separated by session.

    See Also
    ========
    dcmlib.fill_from_dicom, dcmlib.find_a_dicom

    """

    # TODO: add the possibility of updating sources (e.g. anonymize, fix, etc.)
    def get_filepaths(dirpath):
        for root, dirs, files in os.walk(in_dirpath):  # no need to sort
            for name in files:
                yield os.path.join(root, name)

    if verbose > VERB_LVL['none']:
        print(':: Importing sources...')
        print('Input:\t{}'.format(in_dirpath))
        print('Output:\t{}'.format(out_dirpath))
        if clean:
            print('W: Files will be moved!')
    if os.path.exists(in_dirpath):
        # :: analyze directory tree
        dcm_dirpaths = set()
        for filepath in get_filepaths(in_dirpath):
            filename = os.path.basename(filepath)
            is_dicom = dpc.is_dicom(
                filepath,
                allow_dir=False,
                allow_report=True,
                allow_postprocess=True)
            is_zipped, zip_method = dpc.is_compressed_dicom(
                filepath,
                allow_dir=False,
                allow_report=True,
                allow_postprocess=True)
            if is_dicom or is_zipped and zip_method in dpc.UNCOMPRESS_METHODS:
                if subpath:
                    dcm_subpath = dpc.fill_from_dicom(subpath, filepath)
                    dcm_dirpath = os.path.join(out_dirpath, dcm_subpath)
                else:
                    dcm_dirpath = out_dirpath
                if not os.path.exists(dcm_dirpath):
                    os.makedirs(dcm_dirpath)
                if dcm_dirpath not in dcm_dirpaths:
                    if verbose > VERB_LVL['none']:
                        print('Subpath:\t{}'.format(dcm_subpath))
                    dcm_dirpaths.add(dcm_dirpath)
                if not os.path.isfile(os.path.join(dcm_dirpath, filename)) \
                        or force:
                    if clean:
                        shutil.move(filepath, dcm_dirpath)
                    else:
                        shutil.copy(filepath, dcm_dirpath)
                else:
                    if verbose > VERB_LVL['low']:
                        print("II: Output filepath exists. Skipping. " +
                              "Use 'force' argument to override.")
            else:
                name = filepath[len(in_dirpath):]
                if verbose > VERB_LVL['low']:
                    print('WW: Invalid source found \'{}\''.format(name))
    else:
        if verbose > VERB_LVL['none']:
            print('WW: Input path does NOT exists.')
    return dcm_dirpaths


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
    # default subpath
    d_subpath = '{study}/{name}_{date}_{time}_{sys}/dcm'
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
        '-i', '--input', metavar='DIR',
        default=d_input_dir,
        help='set input directory [%(default)s]')
    arg_parser.add_argument(
        '-o', '--output', metavar='DIR',
        default=d_output_dir,
        help='set output directory [%(default)s]')
    arg_parser.add_argument(
        '-c', '--clean',
        action='store_true',
        help='Move DICOM sources instead of copying [%(default)s]')
    arg_parser.add_argument(
        '-s', '--subpath',
        default=d_subpath,
        help='Append DICOM-generated subpath to output [%(default)s]')
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

    import_sources(
        args.input, args.output,
        args.clean, args.subpath,
        args.force, args.verbose)

    end_time = time.time()
    if args.verbose > VERB_LVL['low']:
        print('ExecTime: ', datetime.timedelta(0, end_time - begin_time))


# ======================================================================
if __name__ == '__main__':
    main()
