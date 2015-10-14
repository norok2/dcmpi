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
#import shutil  # High-level file operations
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
import json  # JSON encoder and decoder [JSON: JavaScript Object Notation]

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
import common as dcmlib
import custom_info as custom_info
from dcmpi import INFO
from dcmpi import VERB_LVL
from dcmpi import D_VERB_LVL
from dcmpi import get_first_line


# ======================================================================
def get_info(
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
    if verbose > VERB_LVL['none']:
        print(':: Exporting CUSTOM information ({})...'.format(method))
    if verbose > VERB_LVL['none']:
        print('Input:\t{}'.format(in_dirpath))
    if verbose > VERB_LVL['none']:
        print('Output:\t{}'.format(out_dirpath))
    sources_dict = dcmlib.dcm_sources(in_dirpath)
    groups_dict = dcmlib.group_series(in_dirpath)
    # proceed only if output is not likely to be there
    if not os.path.exists(out_dirpath) or force:
        # :: create output directory if not exists
        if not os.path.exists(out_dirpath):
            os.makedirs(out_dirpath)

        if method == 'pydicom':
            # :: extract session information
            out_filepath = os.path.join(
                out_dirpath, dcmlib.D_SUMMARY + '.' + dcmlib.ID['info'])
            out_filepath += ('.' + dcmlib.JSON_EXT) if type_ext else ''
            info_dict = {}
            # info_dict['_sources'] = sources_dict  # DEBUG
            info_dict['_measurements'] = groups_dict
            try:
                read_next_dicom = True
                idx = -1
                while read_next_dicom:
                    # get last dicom
                    in_filepath = sorted(sources_dict.items())[idx][1][-1]
                    dcm = pydcm.read_file(in_filepath)
                    stop = 'PixelData' in dcm and \
                        'ImageType' in dcm and 'ORIGINAL' in dcm.ImageType
                    if stop:
                        read_next_dicom = False
                    else:
                        idx -= 1

            except Exception as ex:
                print(sources_dict)
                print("EE: failed during get_info (exceptioon: {})".format(ex))
            else:
                # DICOM's-ready information
                info_dict.update(dcmlib.postprocess_info(
                    dcm, custom_info.SESSION, lambda x, p: x.value, verbose))
                # additional information: duration
                field_id = 'Duration'
                try:
                    begin_time = time.mktime(time.strptime(
                        info_dict['BeginDate'] + '_' + info_dict['BeginTime'],
                        '%Y-%m-%d_%H:%M:%S'))
                    end_time = time.mktime(time.strptime(
                        info_dict['EndDate'] + '_' + info_dict['EndTime'],
                        '%Y-%m-%d_%H:%M:%S'))
                    field_val = str(
                        datetime.timedelta(0, end_time - begin_time))
                except:
                    field_val = 'N/A'
                    if verbose > VERB_LVL['low']:
                        print("WW: Cannot process '{}'.".format(field_id))
                finally:
                    info_dict[field_id] = field_val
            if verbose > VERB_LVL['none']:
                out_subpath = out_filepath[len(out_dirpath):]
                print('Info:\t{}'.format(out_subpath))
            with open(out_filepath, 'w') as info_file:
                json.dump(info_dict, info_file, sort_keys=True, indent=4)

            # :: extract acquisition information
            for group_id, group_dict in sorted(groups_dict.items()):
                out_filepath = os.path.join(
                    out_dirpath, group_id + '.' + dcmlib.ID['info'])
                out_filepath += ('.' + dcmlib.JSON_EXT) if type_ext else ''
                info_dict = {}
                info_dict['_series'] = group_dict
                in_filepath = sorted(
                    sources_dict[groups_dict[group_id][0]])[-1]
                try:
                    dcm = pydcm.read_file(in_filepath)
                except:
                    print('EE: failed processing \'{}\''.format(in_filepath))
                else:
                    info_dict.update(dcmlib.postprocess_info(
                        dcm, custom_info.ACQUISITION, lambda x, p: x.value,
                        verbose))
                    # information from protocol
                    if dcmlib.DCM_ID['hdr_nfo'] in dcm:
                        prot_src = dcm[dcmlib.DCM_ID['hdr_nfo']].value
                        prot_dict = dcmlib.parse_protocol(
                            dcmlib.get_protocol(prot_src))
                    else:
                        prot_dict = {}
                    info_dict.update(dcmlib.postprocess_info(
                        prot_dict,
                        custom_info.get_sequence_info(info_dict, prot_dict),
                        None, verbose))
                    # additional information: duration
                    field_id = 'Duration'
                    try:
                        begin_time = time.mktime(time.strptime(
                            info_dict['BeginDate'] + '_' +
                            info_dict['BeginTime'],
                            '%Y-%m-%d_%H:%M:%S'))
                        end_time = time.mktime(time.strptime(
                            info_dict['EndDate'] + '_' +
                            info_dict['EndTime'],
                            '%Y-%m-%d_%H:%M:%S'))
                        field_val = str(
                            datetime.timedelta(0, end_time - begin_time))
                    except:
                        field_val = 'N/A'
                        if verbose > VERB_LVL['low']:
                            print("WW: Cannot process '{}'.".format(field_id))
                    finally:
                        info_dict[field_id] = field_val
                if verbose > VERB_LVL['none']:
                    out_subpath = out_filepath[len(out_dirpath):]
                    print('Info:\t{}'.format(out_subpath))
                with open(out_filepath, 'w') as info_file:
                    json.dump(info_dict, info_file, sort_keys=True, indent=4)

            # :: extract series information
            for src_id, in_filepath_list in sorted(sources_dict.items()):
                out_filepath = os.path.join(
                    out_dirpath, src_id + '.' + dcmlib.ID['info'])
                out_filepath += ('.' + dcmlib.JSON_EXT) if type_ext else ''
                info_dict = {}
                for acq, series in groups_dict.items():
                    if src_id in series:
                        info_dict['_acquisition'] = acq
                    try:
                        dcm = pydcm.read_file(in_filepath)
                    except:
                        print("EE: failed processing '{}'".format(in_filepath))
                    else:
                        info_dict.update(dcmlib.postprocess_info(
                            dcm, custom_info.SERIES, lambda x, p: x.value,
                            verbose))
                if verbose > VERB_LVL['none']:
                    out_subpath = out_filepath[len(out_dirpath):]
                    print('Info:\t{}'.format(out_subpath))
                with open(out_filepath, 'w') as info_file:
                    json.dump(info_dict, info_file, sort_keys=True, indent=4)
        else:
            if verbose > VERB_LVL['none']:
                print("WW: Unknown method '{}'.".format(method))
    else:
        if verbose > VERB_LVL['none']:
            print("II: Output path exists. Skipping. " +
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
            INFO['version'], ', '.join(INFO['authors']), INFO['license']),
        formatter_class=argparse.RawDescriptionHelpFormatter)
    # :: Add POSIX standard arguments
    arg_parser.add_argument(
        '--ver', '--version',
        version='%(prog)s - ver. {}\n{}\n{} {}\n{}'.format(
            INFO['version'], get_first_line(__doc__),
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
        '-m', '--method', metavar='METHOD',
        default=d_method,
        help='set extraction method [%(default)s]')
    arg_parser.add_argument(
        '-t', '--type_ext',
        action='store_true',
        help='add type extension [%(default)s]')
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

    get_info(
        ARGS.input, ARGS.output,
        ARGS.method, ARGS.type_ext,
        ARGS.force, ARGS.verbose)

    end_time = time.time()
    if ARGS.verbose > VERB_LVL['low']:
        print('ExecTime: ', datetime.timedelta(0, end_time - begin_time))
