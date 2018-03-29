#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Extract protocol from DICOM files and store it as text files.

Note: specifically extract sequence protocol as stored by Siemens in their
custom-made 'CSA Series Header Info' DICOM metadata.
This information is relatively easy to parse.
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
import pydicom as pydcm  # PyDicom (Read, modify and write DICOM files.)

# :: External Imports Submodules
# import matplotlib.pyplot as plt  # Matplotlib's pyplot: MATLAB-like syntax
# import mayavi.mlab as mlab  # Mayavi's mlab: MATLAB-like syntax
# import scipy.optimize  # SciPy: Optimization Algorithms
# import scipy.integrate  # SciPy: Integrations facilities
# import scipy.constants  # SciPy: Mathematal and Physical Constants
# import scipy.ndimage  # SciPy: ND-image Manipulation

# :: Local Imports
# from mri_tools.modules.sequences import mp2rage
import dcmpi.utils as utl
from dcmpi import INFO, DIRS
from dcmpi import VERB_LVL, D_VERB_LVL, VERB_LVL_NAMES
from dcmpi import msg, dbg


# ======================================================================
def get_prot(
        in_dirpath,
        out_dirpath,
        method='pydicom',
        type_ext=False,
        force=False,
        verbose=D_VERB_LVL):
    """
    Extract protocol information from DICOM files and store them as text files.

    Parameters
    ==========
    in_dirpath : str
        Path to input directory.
    out_dirpath : str
        Path to output directory.
    method : str (optional)
        | Extraction method. Accepted values:
        * pydicom: Use PyDICOM Python module.
    type_ext : boolean (optional)
        Add type extension to filename.
    force : boolean (optional)
        Force new processing.
    verbose : int (optional)
        Set level of verbosity.

    Returns
    =======
    None.

    """
    msg(':: Exporting PROTOCOL information ({})...'.format(method))
    msg('Input:  {}'.format(in_dirpath))
    msg('Output: {}'.format(out_dirpath))
    sources_dict = utl.dcm_sources(in_dirpath)
    groups_dict = utl.group_series(in_dirpath)
    # proceed only if output is not likely to be there
    if not os.path.exists(out_dirpath) or force:
        # :: create output directory if not exists and extract protocol
        if not os.path.exists(out_dirpath):
            os.makedirs(out_dirpath)
        if method == 'pydicom':
            for group_id, group in sorted(groups_dict.items()):
                in_filepath = sources_dict[group[0]][0]
                out_filepath = os.path.join(
                    out_dirpath, group_id + '.' + utl.ID['prot'])
                out_filepath += ('.' + utl.EXT['txt']) if type_ext else ''
                try:
                    dcm = pydcm.read_file(in_filepath)
                    prot_src = dcm[utl.DCM_ID['hdr_nfo']].value
                    prot_str = utl.get_protocol(prot_src)
                except:
                    msg('E: failed processing \'{}\''.format(in_filepath))
                else:
                    msg('Protocol: {}'.format(out_filepath[len(out_dirpath):]))
                    with open(out_filepath, 'w') as prot_file:
                        prot_file.write(prot_str)
        else:
            msg('W: Unknown method `{}`.'.format(method))
    else:
        msg('I: Skipping existing output path. Use `force` to override.')


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
        action='count', default=d_verbose,
        help='increase the level of verbosity [%(default)s]')
    # :: Add additional arguments
    arg_parser.add_argument(
        '-f', '--force',
        action='store_true',
        help='force new processing [%(default)s]')
    arg_parser.add_argument(
        '-i', '--in_dirpath', metavar='DIR',
        default=d_input_dir,
        help='set input directory [%(default)s]')
    arg_parser.add_argument(
        '-o', '--out_dirpath', metavar='DIR',
        default=d_output_dir,
        help='set output directory [%(default)s]')
    arg_parser.add_argument(
        '-m', '--method', metavar='METHOD',
        default=d_method,
        help='set extraction method [%(default)s]')
    arg_parser.add_argument(
        '-t', '--type_ext',
        action='store_true',
        help='add type extension [%(default)s]')
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

    get_prot(
        args.in_dirpath, args.out_dirpath,
        args.method, args.type_ext,
        args.force, args.verbose)

    exec_time = datetime.datetime.now() - begin_time
    msg('ExecTime: {}'.format(exec_time), args.verbose, VERB_LVL['debug'])


# ======================================================================
if __name__ == '__main__':
    main()
