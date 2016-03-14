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
# import itertools  # Functions creating iterators for efficient looping
# import functools  # Higher-order functions and operations on callable objects
import subprocess  # Subprocess management
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
# from dcmpi import INFO
from dcmpi import VERB_LVL
from dcmpi import D_VERB_LVL

# ======================================================================
# :: General-purposes constants
NO_EXT = ''
TXT_EXT = 'txt'
JSON_EXT = 'json'
DCM_EXT = 'ima'  # DICOM image
DCR_EXT = 'sr'  # DICOM report
NII_EXT = 'nii'
NIZ_EXT = 'nii.gz'

INFO_SEP = '__'
FMT_SEP = '::'

TTY_COLORS = {
    'r': 31, 'g': 32, 'b': 34, 'c': 36, 'm': 35, 'y': 33, 'w': 37, 'k': 30,
    'R': 41, 'G': 42, 'B': 44, 'C': 46, 'M': 45, 'Y': 43, 'W': 47, 'K': 40,
}

D_SUMMARY = 'summary'

PREFIX_ID = {
    'series': 's',
    'acq': 'a', }

D_NUM_DIGITS = 3

# identifiers used by the pre-processing
ID = {
    'dicom': 'dcm',
    'nifti': 'nii',
    'info': 'info',
    'meta': 'meta',
    'prot': 'prot',
    'report': 'report',
    'backup': 'dcm', }

# DICOM indexes
DCM_ID = {
    'pixel_data': (0x7fe0, 0x0010),  # Binary image data
    'hdr_nfo': (0x0029, 0x1020),  # CSA Series Header Info
    'TA': (0x0051, 0x100a),  # Acquisition Time (Duration)
}
# Time difference (in seconds) between two series for them to be considered
#    from different acquisition.
GRACE_PERIOD = 2.0

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
    'bz2': 'bzip2 -d', }

DICOM_BINARY = (
    (0x7fe0, 0x0010),  # PixelData
)

D_ACTIONS = (
    ('get_nifti', ('::i_dirpath', '::o_dirpath', 'dcm2nii', True, True)),
    ('get_meta', ('::i_dirpath', '::o_dirpath', 'pydicom', False,)),
    ('get_prot', ('::i_dirpath', '::o_dirpath', 'pydicom', False,)),
    ('get_info', ('::i_dirpath', '::o_dirpath', 'pydicom', False,)),
    ('report', ('::i_dirpath', '::o_dirpath', 'info', 'pdf',)),
    ('backup', ('::i_dirpath', '::o_dirpath', '7z', False,)))


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
def execute(cmd, use_pipes=True, dry=False, verbose=D_VERB_LVL):
    """
    Execute command and retrieve output at the end of execution.

    Parameters
    ==========
    cmd : str
        Command to execute.
    use_pipes : bool (optional)
        If True, get both stdout and stderr streams from the process.
    dry : bool (optional)
        If True, the command is printed instead of being executed (dry run).
    verbose : int (optional)
        Set level of verbosity.

    Returns
    =======
    p_stdout : str
        The stdout of the process after execution.
    p_stderr : str
        The stderr of the process after execution.

    """
    if dry:
        print('Dry:\t{}'.format(cmd))
    else:
        if verbose > VERB_LVL['low']:
            print('Cmd:\t{}'.format(cmd))
        if use_pipes:
            #            # :: deprecated
            #            proc = os.popen3(cmd)
            #            p_stdout, p_stderr = [item.read() for item in proc[
            # 1:]]
            # :: new style
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True, close_fds=True)
            p_stdout = proc.stdout.read()
            p_stderr = proc.stderr.read()
            if verbose > VERB_LVL['medium']:
                print('stdout:\t{}'.format(p_stdout))
            if verbose > VERB_LVL['medium']:
                print('stderr:\t{}'.format(p_stderr))
        else:
            p_stdout = p_stderr = None
            #            # :: deprecated
            #            os.system(cmd)
            # :: new style
            subprocess.call(cmd, shell=True)
    return p_stdout, p_stderr


# ======================================================================
def string_between(
        text,
        begin_str,
        end_str,
        incl_begin=False,
        incl_end=False,
        greedy=True):
    """
    Isolate the string contained between two tookens
    """
    incl_begin = len(begin_str) if not incl_begin else 0
    incl_end = len(end_str) if incl_end else 0
    if begin_str in text and end_str in text:
        if greedy:
            text = text[
                   text.find(begin_str) + incl_begin:
                   text.rfind(end_str) + incl_end]
        else:
            text = text[
                   text.rfind(begin_str) + incl_begin:
                   text.find(end_str) + incl_end]
    else:
        text = ''
    return text


# ======================================================================
def tty_colorify(
        text,
        color=None):
    """
    Add color TTY-compatible color code to a string, for pretty-printing.

    Parameters
    ==========
    text: str
        The text to be colored.
    color : str or int or None
        | A string or number for the color coding.
        | Lowercase letters modify the forground color.
        | Uppercase letters modify the background color.
        | Available colors:
        * r/R: red
        * g/G: green
        * b/B: blue
        * c/C: cyan
        * m/M: magenta
        * y/Y: yellow (brown)
        * k/K: black (gray)
        * w/W: white (gray)

    Returns
    =======
        The colored string.

    see also: TTY_COLORS
    """
    if color in TTY_COLORS:
        tty_color = TTY_COLORS[color]
    elif color in TTY_COLORS.values():
        tty_color = color
    else:
        tty_color = None
    if tty_color and sys.stdout.isatty():
        return '\x1b[1;{color}m{}\x1b[1;m'.format(text, color=tty_color)
    else:
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
            raise
        # check if it is a DICOM report
        is_report = True if 'PixelData' not in dcm else False
        if is_report and not allow_report:
            raise
        # check if it is a DICOM postprocess image  # TODO: improve this
        is_postprocess = True if 'MagneticFieldStrength' not in dcm else False
        if is_postprocess and not allow_postprocess:
            raise
    except:
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

    Args:
        filepath (str): The path to the file.
        allow_dir (bool): accept DICOM directories as valid
        allow_report (bool): accept DICOM reports as valid
        allow_postprocess (bool): accept DICOM post-process data as valid
        tmp_path (str): The path for temporary extraction.
        known_methods:

    Returns:

    """
    """
    Check if the compressed filepath contains a valid DICOM file.
    """
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
            is_a_compressed, compression = is_compressed_dicom(
                filename,
                allow_dir=allow_dir,
                allow_report=allow_report,
                allow_postprocess=allow_postprocess)
            if is_a_dicom:
                dcm_filename = filename
                break
            elif is_a_compressed:
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
    fields_dict = {
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
        out_str = format_str
        if extra_fields:
            for item in dir(dcm):
                if item[0].isupper():
                    fields_dict[item] = (item, None, None)
        for field_id, fields in sorted(fields_dict.items()):
            pattern = r'\{{}.*?\}'.format(field_id)
            field_match = re.search(pattern, out_str)
            if field_match:
                matched = out_str[field_match.start():field_match.end()]
                dcm_id, func, field_fmt = fields \
                    if field_id in fields_dict else ('', None, '')
                if FMT_SEP in matched:
                    field_fmt = matched.split(FMT_SEP)[1][:-1]
                field_replace = getattr(dcm, dcm_id) \
                    if dcm_id in dcm else matched
                if func:
                    field_replace = func(field_replace, field_fmt)
                out_str = out_str.replace(matched, field_replace)
    finally:
        if os.path.isfile(temp_filepath):
            os.remove(temp_filepath)
        elif os.path.isfile(dcm_filepath):
            os.remove(dcm_filepath)
    return out_str


# ======================================================================
def get_date(text):
    """
    Extract date (return tm_struct) from 'Date' DICOM strings.
    """
    tm_struct = time.strptime(text, '%Y%m%d')
    return tm_struct


# ======================================================================
def get_time(text):
    """
    Extract time (return tm_struct) from 'Time' DICOM strings.
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
        groups_dict = {}
        with open(summary_filepath, 'r') as summary_file:
            groups_dict = json.load(summary_file)
    else:
        sources_dict = dcm_sources(dirpath)
        groups_dict = {}
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
                        if group_id not in groups_dict:
                            groups_dict[group_id] = []
                        group_num += 1
                    # print('{:32s}\t{:32s}'.format(group_id, src_id))
                    groups_dict[group_id].append(src_id)
                    last_time = curr_time
                    last_prot_name = curr_prot_name
                    # last_duration = get_duration(dcm[DCM_ID['TA']])
                elif is_report:
                    group_id = dcm.SeriesDescription
                    if group_id not in groups_dict:
                        groups_dict[group_id] = []
                    groups_dict[group_id].append(src_id)
        # :: save grouping to file
        if summary_filepath:
            if verbose > VERB_LVL['none']:
                print('Brief:\t{}'.format(summary_filepath))
            with open(summary_filepath, 'w') as summary_file:
                json.dump(groups_dict, summary_file, sort_keys=True, indent=4)
    return groups_dict


# ======================================================================
def dcm_sources(dirpath):
    """
    Create sources dictionary from files in dirpath.

    Args:
        dirpath (str): The path to the directory

    Returns:
        (dict):
    """
    sources_dict = {}
    for src_id in sorted(os.listdir(dirpath)):
        src_dirpath = os.path.join(dirpath, src_id)
        if os.path.isdir(src_dirpath):
            sources_dict[src_id] = [
                os.path.join(src_dirpath, filename)
                for filename in sorted(os.listdir(src_dirpath))]
    return sources_dict


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
    out_dict = {}
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
                if key in out_dict:
                    val = out_dict[key]
                else:
                    val = []
                val.append((indexes, auto_convert(value, '""', '""')))
            else:
                val = auto_convert(value, '""', '""')
            if key:
                out_dict[key] = val
    return out_dict


# ======================================================================
def postprocess_info(
        source_dict,
        postproc_dict,
        access_val=None,
        access_val_params=None,
        verbose=D_VERB_LVL):
    """
    Extract information from DICOM according to specific instruction dict.

    Parameters
    ==========
    source_dict : dict
        Dictionary containing the information to post-process.
    postproc_dict : dict
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
    info_dict : dict
        The postprocessed information.

    """
    info_dict = {}
    for pp_id, postproc in sorted(postproc_dict.items()):
        src_id, fmt, fmt_params = postproc
        if src_id in source_dict:
            if access_val:
                field_val = access_val(source_dict[src_id], access_val_params)
            else:
                field_val = source_dict[src_id]
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
        info_dict[pp_id] = field_val
    return info_dict


# ======================================================================
if __name__ == '__main__':
    print(__doc__)
