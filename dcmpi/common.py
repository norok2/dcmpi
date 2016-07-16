#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Common library of DCMPI.
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
import sys  # System-specific parameters and functions
import shutil  # High-level file operations
# import math  # Mathematical functions
import time  # Time access and conversions
import datetime  # Basic date and time types
import string  # Common string operations
import re  # Regular expression operations
# import operator  # Standard operators as functions
# import collections  # High-performance container datatypes
# import argparse  # Parser for command-line options, arguments and subcommands
import itertools  # Functions creating iterators for efficient looping
# import functools  # Higher-order functions and operations on callable objects
import subprocess  # Subprocess management
# import multiprocessing  # Process-based parallelism
# import csv  # CSV File Reading and Writing [CSV: Comma-Separated Values]
import json  # JSON encoder and decoder [JSON: JavaScript Object Notation]
# import unittest  # Unit testing framework
import doctest  # Test interactive Python examples
import shlex  # Simple lexical analysis

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
# from dcmpi_cli import INFO
from dcmpi import VERB_LVL
from dcmpi import D_VERB_LVL

# ======================================================================
# :: General-purposes constants
EXT = {
    'None': '',
    'txt': 'txt',
    'json': 'json',
    'dcm': 'ima',  # DICOM image
    'dcr': 'sr',  # DICOM report
    'niz': 'nii.gz',
    'nii': 'nii'
}

INFO_SEP = '__'
FMT_SEP = '::'

D_SUMMARY = 'summary'

PREFIX_ID = {
    'series': 's',
    'acq': 'a',}

D_NUM_DIGITS = 3

# identifiers used by the pre-processing
ID = {
    'dicom': 'dcm',
    'nifti': 'nii',
    'info': 'info',
    'meta': 'meta',
    'prot': 'prot',
    'report': 'report',
    'backup': 'dcm',}

# DICOM indexes
DCM_ID = {
    'pixel_data': (0x7fe0, 0x0010),  # Binary image data
    'hdr_nfo': (0x0029, 0x1020),  # CSA Series Header Info
    'TA': (0x0051, 0x100a),  # Acquisition Time (Duration)
}

# DICOM series with nominal absolute time of acquisition differing more than
#   GRACE_PERIOD are considered as originating from different acquisitions.
GRACE_PERIOD = 2.0  # s

PROT_BEGIN = '<XProtocol>'
PROT_END = '### ASCCONV END ###" \n    }\n  }\n}\n'

# :: station name
STATION = {
    'SEPTEMSYS': '7T_Magnetom',
    'TRIOSYS': '3T_Prisma',
    'MRC40540': '3T_Verio-1',
    'MRC40635': '3T_Verio-2',
    'TODO': '3T_Skyra',
}

UNCOMPRESS_METHODS = {
    'gz': 'gunzip',
    'xz': 'unxz',
    'lzma': 'unlzma',
    'bz2': 'bzip2 -d',}

DICOM_BINARY = (
    (0x7fe0, 0x0010),  # PixelData
)


# ======================================================================
def _nominal_B0(val):
    """
    Infer Nominal Magnetic Field Strength from exact one.
    """
    val = float(val)
    if abs(round(val) - round(val, 1)) > 0:
        val = round(val, 1)
    else:
        val = int(round(val))
    return val


# ======================================================================
def has_decorator(text, pre_decor='"', post_decor='"'):
    """
    Determine if a string is delimited by some characters (decorators).
    """
    return text.startswith(pre_decor) and text.endswith(post_decor)


# ======================================================================
def auto_convert(val_str, pre_decor=None, post_decor=None):
    """
    Convert value to numeric if possible, or strip delimiters from strings.
    """
    if pre_decor and post_decor and \
            has_decorator(val_str, pre_decor, post_decor):
        val = val_str[len(pre_decor):-len(post_decor)]
    else:
        try:
            val = int(val_str)
        except ValueError:
            try:
                val = float(val_str)
            except ValueError:
                try:
                    val = complex(val_str)
                except ValueError:
                    val = val_str
    return val


# ======================================================================
def execute(
        cmd,
        get_pipes=True,
        dry=False,
        verbose=D_VERB_LVL):
    """
    Execute command and retrieve/print output at the end of execution.

    Args:
        cmd (str|unicode|list[str]): Command to execute.
        get_pipes (bool): Get stdout and stderr streams from the process.
            If True, the program flow is halted until the process is completed.
            Otherwise, the process is spawn in background, continuing execution.
        dry (bool): Print rather than execute the command (dry run).
        verbose (int): Set level of verbosity.

    Returns:
        ret_code (str): if get_pipes, the return code of the command.
        p_stdout (str|unicode|None): if get_pipes, the stdout of the process.
        p_stderr (str|unicode|None): if get_pipes, the stderr of the process.
    """
    p_stdout, p_stderr, ret_code = None, None, None
    # ensure cmd is a list of strings
    try:
        cmd = shlex.split(cmd)
    except AttributeError:
        pass

    if dry:
        print('$$ {}'.format(' '.join(cmd)))
    else:
        if verbose >= VERB_LVL['medium']:
            print('>> {}'.format(' '.join(cmd)))

        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False, close_fds=True)

        if get_pipes:
            # handle stdout
            p_stdout = ''
            while proc.poll() is None:
                stdout_buffer = proc.stdout.read(1)
                p_stdout += stdout_buffer
                if verbose >= VERB_LVL['medium']:
                    sys.stdout.write(stdout_buffer)
                    sys.stdout.flush()
            # handle stderr
            p_stderr = proc.stderr.read()
            if verbose >= VERB_LVL['high']:
                print(p_stderr)
            # finally get the return code
            ret_code = proc.returncode

    return p_stdout, p_stderr, ret_code


# ======================================================================
def check_redo(
        in_filepaths,
        out_filepaths,
        force=False):
    """
    Check if input files are newer than output files, to force calculation.

    Args:
        in_filepaths (list[str|unicode]): Input filepaths for computation.
        out_filepaths (list[str|unicode]): Output filepaths for computation.
        force (bool): Force computation to be re-done.

    Returns:
        force (bool): True if the computation is to be re-done.

    Raises:
        IndexError: If the input filepath list is empty.
        IOError: If any of the input files do not exist.
    """
    # todo: include output_dir autocreation
    # check if input is not empty
    if not in_filepaths:
        raise IndexError('List of input files is empty.')

    # check if input exists
    for in_filepath in in_filepaths:
        if not os.path.exists(in_filepath):
            raise IOError('Input file does not exists.')

    # check if output exists
    if not force:
        for out_filepath in out_filepaths:
            if out_filepath:
                if not os.path.exists(out_filepath):
                    force = True
                    break

    # check if input is older than output
    if not force:
        for in_filepath, out_filepath in \
                itertools.product(in_filepaths, out_filepaths):
            if in_filepath and out_filepath:
                if os.path.getmtime(in_filepath) \
                        > os.path.getmtime(out_filepath):
                    force = True
                    break
    return force


# ======================================================================
def string_between(
        text,
        begin_str,
        end_str,
        incl_begin=False,
        incl_end=False,
        greedy=True):
    """
    Isolate the string contained between two tokens

    Args:
        text (str): String to parse
        begin_str (str): Token at the beginning
        end_str (str): Token at the ending
        incl_begin (bool): Include 'begin_string' in the result
        incl_end (bool): Include 'end_str' in the result.
        greedy (bool): Output the largest possible string.

    Returns:
        text (str): The string contained between the specified tokens (if any)

    Examples:
        >>> string_between('roses are red violets are blue', 'ses', 'lets')
        ' are red vio'
        >>> string_between('roses are red, or not?', 'a', 'd')
        're re'
        >>> string_between('roses are red, or not?', ' ', ' ')
        'are red, or'
        >>> string_between('roses are red, or not?', ' ', ' ', greedy=False)
        'are'
        >>> string_between('roses are red, or not?', 'r', 'r')
        'oses are red, o'
        >>> string_between('roses are red, or not?', 'r', 'r', greedy=False)
        'oses a'
        >>> string_between('roses are red, or not?', 'r', 's', True, False)
        'rose'
    """
    incl_begin = len(begin_str) if not incl_begin else 0
    incl_end = len(end_str) if incl_end else 0
    if begin_str in text and end_str in text:
        if greedy:
            begin = text.find(begin_str) + incl_begin
            end = text.rfind(end_str) + incl_end
        else:
            begin = text.find(begin_str) + incl_begin
            end = text[begin:].find(end_str) + incl_end + begin
        text = text[begin:end]
    else:
        text = ''
    return text


# ======================================================================
def is_dicom(
        filepath,
        allow_dir=False,
        allow_report=False,
        allow_postprocess=False):
    """
    Check if the filepath is a valid DICOM file.

    Args:
        filepath (str): The path to the file.
        allow_dir (bool): accept DICOM directories as valid
        allow_report (bool): accept DICOM reports as valid
        allow_postprocess (bool): accept DICOM post-process data as valid

    Returns:
        (bool) True if the file is a valid DICOM, false otherwise.
    """
    try:
        dcm = pydcm.read_file(filepath)
        # check if it is a DICOM dir.
        is_dir = True if 'DirectoryRecordSequence' in dcm else False
        if is_dir and not allow_dir:
            raise StopIteration
        # check if it is a DICOM get_report
        is_report = True if 'PixelData' not in dcm else False
        if is_report and not allow_report:
            raise StopIteration
        # check if it is a DICOM postprocess image  # TODO: improve this
        is_postprocess = True if 'MagneticFieldStrength' not in dcm else False
        if is_postprocess and not allow_postprocess:
            raise StopIteration
    except StopIteration:
        return False
    else:
        return True


# ======================================================================
def is_compressed_dicom(
        filepath,
        allow_dir=False,
        allow_report=False,
        allow_postprocess=False,
        tmp_path='/tmp',
        known_methods=UNCOMPRESS_METHODS):
    """
    Check if the compressed filepath contains a valid DICOM file.

    Args:
        filepath (str): The path to the file.
        allow_dir (bool): accept DICOM directories as valid
        allow_report (bool): accept DICOM reports as valid
        allow_postprocess (bool): accept DICOM post-process data as valid
        tmp_path (str): The path for temporary extraction.
        known_methods:

    Returns:

    """
    # todo: fix docs
    filename = os.path.basename(filepath)
    temp_filepath = os.path.join(tmp_path, filename)
    test_filepath = os.path.splitext(temp_filepath)[0]
    shutil.copy(filepath, temp_filepath)
    result = False
    for compression, cmd in known_methods.items():
        cmd += ' {}'.format(temp_filepath)
        execute(cmd)
        if os.path.isfile(test_filepath):
            result = is_dicom(
                test_filepath, allow_dir, allow_report, allow_postprocess)
            os.remove(test_filepath)
            break
    if os.path.isfile(temp_filepath):
        compression = None
        os.remove(temp_filepath)
    return result, compression


# ======================================================================
def find_a_dicom(
        dirpath,
        allow_dir=False,
        allow_report=False,
        allow_postprocess=False):
    """
    Find a DICOM file (recursively) in the directory. Assume same experiment.
    """
    dcm_filename, compression = '', ''
    for root, dirs, files in sorted(os.walk(dirpath)):
        for name in files:
            filename = os.path.join(root, name)
            is_a_dicom = is_dicom(
                filename,
                allow_dir=allow_dir,
                allow_report=allow_report,
                allow_postprocess=allow_postprocess)
            if not is_a_dicom:
                is_a_compressed, compression = is_compressed_dicom(
                    filename,
                    allow_dir=allow_dir,
                    allow_report=allow_report,
                    allow_postprocess=allow_postprocess)
            else:
                is_a_compressed = False
            if is_a_dicom or is_a_compressed:
                dcm_filename = filename
                break
        if dcm_filename:
            break
    if not dcm_filename:
        print("EE: A DICOM file was not found in '{}'.".format(dirpath))
    return dcm_filename, compression


# ======================================================================
def fill_from_dicom(
        format_str,
        filepath,
        compression=None,
        extra_fields=False,
        tmp_path='/tmp'):
    """
    Fill a format string with information from a DICOM file.

    Parameters
    ==========
    format_str : str
        | String used to set a format.
        | Field syntax: [FIELD::FORMAT] (::FORMAT part is optional)
        | Accepted fields (including accepted formats):
        * study : Study Description : 2-int comma-sep. range for slicing.
        * date : Study Date. Format : anything accepted by 'strftime'.
        * time : Study Time. Format : anything accepted by 'strftime'.
        * name : Patient Name. Format : 'mpicbs' to guess ID (only subjects).
        * sys : StationName. Format : 'mpicbs' to guess local names.
    dcm_filepath : str
        DICOM file where to get information from.
    compression : str or None (optional)
        Determine the (de)compression method used to access the data.
    extra_fields : bool (optional)
        | If True, accept fields directly from DICOM. No format is supported.
        | Note that this feature MUST be used with care.

    Returns
    =======
    The formatted string.

    """
    fields = {
        'study': (
            'StudyDescription',
            lambda t, f:  # slice according to 2-int tuple set in 'f'
            t[int(f.split(',')[0]):int(f.split(',')[1])] if f else t,
            ''),
        'date': (
            'StudyDate',
            lambda t, f: time.strftime(f, get_date(t)),
            '%Y-%m-%d'),
        'time': (
            'StudyTime',
            lambda t, f: time.strftime(f, get_time(t)),
            '%H-%M'),
        'name': (
            'PatientName',
            lambda t, f:
            t[:4] if f == 'mpicbs' and (t[3] == 'T' or t[3] == 'X') else t,
            'mpicbs'),
        'sys': (
            'StationName',
            lambda t, f: STATION[t] if f == 'mpicbs' and t in STATION else t,
            'mpicbs'),
    }

    filename = os.path.basename(filepath)
    temp_filepath = os.path.join(tmp_path, filename)
    shutil.copy(filepath, temp_filepath)
    if compression and compression in UNCOMPRESS_METHODS:
        dcm_filepath = os.path.splitext(temp_filepath)[0]
        cmd = UNCOMPRESS_METHODS[compression] + ' {}'.format(temp_filepath)
        execute(cmd)
    else:
        dcm_filepath = temp_filepath
    try:
        dcm = pydcm.read_file(dcm_filepath)
    except:
        print('EE: Could not open DICOM file: {}.'.format(dcm_filepath))
        out_str = ''
    else:
        if extra_fields:
            for item in dir(dcm):
                if item[0].isupper():
                    fields[item] = (item, None, None)
        format_kwargs = {}
        for field_id, field_formatter in sorted(fields.items()):
            dcm_id, fmt_func, field_fmt = field_formatter
            try:
                format_kwargs[field_id] = \
                    fmt_func(getattr(dcm, dcm_id), field_fmt) \
                        if fmt_func else getattr(dcm, dcm_id)
            except TypeError:
                format_kwargs[field_id] = getattr(dcm, dcm_id)
        out_str = format_str.format(**format_kwargs)
    finally:
        if os.path.isfile(temp_filepath):
            os.remove(temp_filepath)
        elif os.path.isfile(dcm_filepath):
            os.remove(dcm_filepath)
    return out_str


# ======================================================================
def get_date(text):
    """
    Extract the date from 'Date' DICOM strings.

    Args:
        text (str): The input string.

    Returns:
        tm_struct (struct_time): The date information.
    """
    tm_struct = time.strptime(text, '%Y%m%d')
    return tm_struct


# ======================================================================
def get_time(text):
    """
    Extract the time from 'Time' DICOM strings.

    Args:
        text (str): The input string.

    Returns:
        tm_struct (time.struct_time): The date information.
    """
    tm_struct = time.strptime(text, '%H%M%S.%f')
    return tm_struct


# ======================================================================
def get_datetime_sec(text):
    """
    Extract date and time (in sec) from joined 'Date' and 'Time' DICOM strings.
    """
    tm_struct = time.strptime(text, '%Y%m%d%H%M%S.%f')
    time_sec = time.mktime(tm_struct)
    return time_sec


# ======================================================================
def get_duration_sec(text):
    """
    Extract duration information from Siemens's custom DICOM string.
    """
    # remove initial label string 'TA '
    text = text[len('TA '):]
    # search for multiplier
    if '*' in text:
        text, multiplier = text.split('*')
    else:
        multiplier = 1
    time_sec = 0.0
    # parse remaining string (should be: ss.msec|mm:ss|hh:mm:ss)
    if ':' in text:
        for i, val in enumerate(text.split(':')[::-1]):
            time_sec += float(val) * 60 ** i
    else:
        time_sec += float(text)
    # apply multipliers
    time_sec *= float(multiplier)
    return round(time_sec)


# ======================================================================
def get_duration(text):
    """
    Extract duration information from Siemens's custom DICOM string.
    """
    return str(datetime.timedelta(0, get_duration_sec(text)))


# ======================================================================
def group_series(
        dirpath,
        save_filepath=None,
        force=False,
        verbose=D_VERB_LVL):
    """
    Group series according to acquisition.
    """
    summary_filepath = os.path.join(dirpath, save_filepath) \
        if save_filepath else ''
    if os.path.exists(summary_filepath) and not force:
        # :: load grouping from file
        groups = {}
        with open(summary_filepath, 'r') as summary_file:
            groups = json.load(summary_file)
    else:
        sources_dict = dcm_sources(dirpath)
        groups = {}
        group_num = 1
        last_time = 0
        last_prot_name = ''
        for src_id, sources in sorted(sources_dict.items()):
            src_dcm = sources[0]
            try:
                dcm = pydcm.read_file(src_dcm)
            except:
                if verbose > VERB_LVL['low']:
                    print('WW: failed processing \'{}\''.format(src_dcm))
            else:
                is_acquisition = DCM_ID['TA'] in dcm \
                                 and 'AcquisitionDate' in dcm \
                                 and 'AcquisitionTime' in dcm \
                                 and 'ProtocolName' in dcm
                is_report = 'SeriesDescription' in dcm \
                            and not DCM_ID['pixel_data'] in dcm
                if is_acquisition:
                    curr_time = get_datetime_sec(
                        dcm.AcquisitionDate + dcm.AcquisitionTime)
                    curr_prot_name = dcm.ProtocolName
                    is_new_group = (curr_time - last_time > GRACE_PERIOD) or \
                                   (curr_prot_name != last_prot_name)
                    if is_new_group:
                        group_id = INFO_SEP.join(
                            (PREFIX_ID['acq'] + '{:0{size}d}'.format(
                                group_num, size=D_NUM_DIGITS),
                             dcm.ProtocolName))
                        if group_id not in groups:
                            groups[group_id] = []
                        group_num += 1
                    # print('{:32s}\t{:32s}'.format(group_id, src_id))
                    groups[group_id].append(src_id)
                    last_time = curr_time
                    last_prot_name = curr_prot_name
                    # last_duration = get_duration(dcm[DCM_ID['TA']])
                elif is_report:
                    group_id = dcm.SeriesDescription
                    if group_id not in groups:
                        groups[group_id] = []
                    groups[group_id].append(src_id)
        # :: save grouping to file
        if summary_filepath:
            if verbose > VERB_LVL['none']:
                print('Brief:\t{}'.format(summary_filepath))
            with open(summary_filepath, 'w') as summary_file:
                json.dump(groups, summary_file, sort_keys=True, indent=4)
    return groups


# ======================================================================
def dcm_sources(dirpath):
    """
    Create sources dictionary from files in dirpath.

    Args:
        dirpath (str): The path to the directory

    Returns:
        (dict):
    """
    sources = {}
    for src_id in sorted(os.listdir(dirpath)):
        src_dirpath = os.path.join(dirpath, src_id)
        if os.path.isdir(src_dirpath):
            sources[src_id] = [
                os.path.join(src_dirpath, filename)
                for filename in sorted(os.listdir(src_dirpath))]
    return sources


# ======================================================================
def dcm_dump(
        dcm,
        mask=DICOM_BINARY):
    """


    Args:
        dcm:
        mask:

    Returns:

    """
    dump = {}
    for field in dcm:
        tag = tuple([int(x, 0x10) for x in str(field.tag)[1:-1].split(', ')])
        key = filter(lambda x: x not in " []'-", str(field.name))
        try:
            val = field.value
            if isinstance(val, str):
                val = filter(lambda x: x in string.printable, val)
                # val = val.encode('string-escape')
            json.dumps(val)
        except:
            val = []
            for item in field.value:
                val.append(dcm_dump(item, mask))

        if tag not in mask:
            if key == 'Unknown' or not key:
                key = '_(0x{:04x},0x{:04x})'.format(*tag)
            dump[key] = [val]
    return dump


# ======================================================================
def dcm_merge_info(
        info,
        new_info):
    """

    """
    for key, val in new_info.items():
        if key not in info:
            info[key] = val
        elif val[0] not in info[key]:
            info[key] += val
    return info


# ======================================================================
def get_protocol(src_str):
    """
    Extract protocol information from CSA Series Header Info
    """
    prot_str = string_between(
        src_str.decode('ascii', errors='ignore'),
        PROT_BEGIN, PROT_END,
        True, True)
    return prot_str


# ======================================================================
def parse_protocol(src_str):
    """
    Parse protocol information and save to a dictionary.

    TODO: improve array support?
    """
    info = {}
    for line in src_str.split('\n'):
        equal_pos = line.find('=')
        # check that lines contain a key=val pair AND is not a comment (#)
        if equal_pos >= 0 and line[0] != '#':
            name = line[:equal_pos].strip()
            value = line[equal_pos + 1:].strip()
            # generate proper key
            key = ''
            indexes = []
            for num, field in enumerate(name.split('.')):
                sep1, sep2 = field.find('['), field.find(']')
                is_array = (True if sep1 != sep2 else False)
                if is_array:
                    indexes.append(int(field[sep1 + 1:sep2]))
                key += '.' + (field[:sep1] + '[]' if is_array else field)
            key = key[1:]
            # put data to dict
            if indexes:
                if key in info:
                    val = info[key]
                else:
                    val = []
                val.append((indexes, auto_convert(value, '""', '""')))
            else:
                val = auto_convert(value, '""', '""')
            if key:
                info[key] = val
    return info


# ======================================================================
def postprocess_info(
        sources,
        formats,
        access_val=None,
        access_val_params=None,
        verbose=D_VERB_LVL):
    """
    Extract information from DICOM according to specific instruction dict.

    Parameters
    ==========
    sources : dict
        Dictionary containing the information to post-process.
    formats : dict
        | Dictionary containing the following information:
        * key: The name of the information
        * | val: (source_key, format_function, format_function_parameters)
          | - source_key: The key used to retrieve information from source
          | - format_function(val, param): Post-processing function
          | - format_function_parameters: Additional function parameters
    access_val : func(val, params) (optional)
        A function used as an helper to access data in the source dict.
    access_val_params : tuple (optional)
        A tuple of the parameters to be passed to the access_val function.
    verbose : int (optional)
        Set level of verbosity.

    Returns
    =======
    info : dict
        The postprocessed information.

    """
    info = {}
    for pp_id, postproc in sorted(formats.items()):
        src_id, fmt, fmt_params = postproc
        if src_id in sources:
            if access_val:
                field_val = access_val(sources[src_id], access_val_params)
            else:
                field_val = sources[src_id]
            try:
                if fmt:
                    field_val = fmt(field_val, fmt_params)
            except:
                if verbose > VERB_LVL['low']:
                    print('WW: Unable to post-process \'{}\'.'.format(src_id))
        else:
            field_val = 'N/A'
            if verbose > VERB_LVL['low']:
                print('WW: \'\' field not found.'.format(src_id))
        info[pp_id] = field_val
    return info


# ======================================================================
if __name__ == '__main__':
    print(__doc__)
