#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Analyze DICOM info to check a given match and performing the specified action.
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
# import sys  # System-specific parameters and functions
# import shutil  # High-level file operations
# import platform  # Access to underlying platform’s identifying data
# import locale  # Internationalization services
# import math  # Mathematical functions
import time  # Time access and conversions
import datetime  # Basic date and time types
import re  # Regular expression operations
# import operator  # Standard operators as functions
# import collections  # High-performance container datatypes
import argparse  # Parser for command-line options, arguments and sub-commands
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
import pydicom as pydcm  # PyDicom (Read, modify and write DICOM files.)

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
from dcmpi import INFO, DIRS
from dcmpi import VERB_LVL, D_VERB_LVL, VERB_LVL_NAMES
from dcmpi import msg, dbg


# ======================================================================
def get_email_txt(
        email_from='',
        email_to='',
        email_cc='',
        email_bcc='',
        signature='A. Friend',
        session=None,
        dirpath=None,
        deadline=None,
        delay_days=10):
    """

    Args:
        email_from ():
        email_to ():
        email_cc ():
        email_bcc ():
        signature ():
        session ():
        dirpath ():
        deadline ():
        delay_days ():

    Returns:

    """
    msg = 'EOF\n'
    session = " from: '{}'".format(session) if session else ''
    dirpath = ' in:\n{}'.format(dirpath) if dirpath else '.'
    if not deadline:
        deadline = datetime.date.strftime(
            datetime.datetime.now() + datetime.timedelta(days=delay_days),
            '%A %d %B %Y')
    msg += 'Subject:MR data{} available\n'.format(session)
    if email_from:
        msg += 'From:{}\n'.format(email_from)
    if email_to:
        msg += 'To:{}\n'.format(email_to)
    if email_cc:
        msg += 'Cc:{}\n'.format(email_cc)
    if email_bcc:
        msg += 'Bcc:{}\n'.format(email_bcc)
    msg += 'Dear user,\n\n'
    msg += 'The data you acquired is now available{}\n\n'.format(dirpath)
    msg += 'IMPORTANT: The files will be archived on {}.\n'.format(deadline)
    msg += 'Afterwards, it can only be fetched through a lengthy process.\n'
    msg += 'Please make sure to get your personal copy now.\n\n'
    msg += 'Have a nice day.\n\n{}\n'.format(signature)
    msg += 'EOF\n'
    return msg


# ======================================================================
def send_mail_dcm(
        dcm_filepath,
        email_addrs=None,
        force=False,
        verbose=D_VERB_LVL):
    """
    Send an email when the measurement was processed.
    """
    recipient_fields = (
        'OperatorsName', 'PerformingPhysicianName', 'ReferringPhysicianName')
    session_fields = (
        ('PatientName',
         lambda t: t[:4] if (t[3] == 'T' or t[3] == 'X') else t),
        ('StudyDate',
         lambda t: time.strftime('%Y-%m-%d', time.strptime(t, '%Y%m%d'))),
        ('StudyTime',
         lambda t: time.strftime('%H-%M', time.strptime(t, '%H%M%S.%f'))),
        ('StationName',
         lambda t: utl.STATION[t] if t in utl.STATION else t),
        ('StudyDescription',
         lambda t: t),
    )
    try:
        dcm = pydcm.read_file(dcm_filepath)
        # get recipient
        recipient = ''
        for key in recipient_fields:
            name = getattr(dcm, key) if key in dcm else ''
            if re.match(r'[^@]+@[^@]+\.[^@]+', name):
                recipient = name
                break
        if not recipient:
            raise ValueError('Could not find a recipient.')
        # get session information
        session_info = []
        for key, func in session_fields:
            if key in dcm:
                session_info.append(func(getattr(dcm, key)))
        sample_id = utl.INFO_SEP.join(session_info[:-1])
        study_id = session_info[-1]
        session = '{} / {}'.format(study_id, sample_id)
        # get dirpath
        dirpath = os.sep.join(dcm_filepath.split(os.sep)[:-2])
    except Exception as ex:
        print(ex)
        msg('E: Could not get information from `{}`.'.format(dcm_filepath))
    else:
        cmd = 'sendmail -t <<{}'.format(
            get_email_txt(
                email_from=recipient,
                email_to=recipient,
                session=session,
                dirpath=dirpath))
        if email_addrs is None or email_addrs.strip().lower() == \
                recipient.strip().lower():
            subprocess.call(cmd, shell=True)
            msg('I: Email sent to: <{}>.'.format(recipient))
        else:
            print(email_addrs)
            msg('W: Email was NOT sent to: <{}>.'.format(recipient))
            msg(' : (you asked only for recipient <{}>).'.format(email_addrs))


# ======================================================================
def dcm_analyze_dir(
        dirpath,
        match='{"_concat":"and"}',
        action='',
        force=False,
        verbose=D_VERB_LVL):
    """
    Analyze a DICOM, performing an action if its data match the request.

    Args:
        dirpath (str): Directory where to look for DICOM files.
        match (str): A JSON-encoded dict with matching information.
            Any key not starting with `_` should specify a DICOM field, while
            the val should contain a regular expression.
            Keys starting with `_` contain special directives:
             - `_concat` (str): the concatenation method for matching rules.
               Accepted values are: ['and'|'or']
        action (str): Action to be performed.
            Accepted values are:
             - send_email: send an email to the first e-mail found.
             - dcmpi_cli: run dcmpi_cli pipeline.
        force (bool): Force new processing.
        verbose (int): Set level of verbosity.

    Returns:
        None.
    """
    dcm_filepath = utl.find_a_dicom(dirpath)[0]
    try:
        dcm = pydcm.read_file(dcm_filepath)
        # check matching
        conditions = json.loads(match)
        concat = conditions.pop('_concat').lower() \
            if '_concat' in conditions else 'and'
        if concat == 'and':
            matched = True
            for key, val in conditions.items():
                name = getattr(dcm, key) if key in dcm else ''
                msg('Match `{}`:`{}` (read:`{}`)'.format(key, val, name))
                if not re.match(val, name):
                    matched = False
                    break
        elif concat == 'or':
            matched = False
            for key, val in conditions.items():
                name = getattr(dcm, key) if key in dcm else ''
                if re.match(val, name):
                    matched = True
                    break
        else:
            raise ValueError('Unknown concatenation method.')
    except Exception as ex:
        print(ex)
        msg('E: Could not get information from `{}`.'.format(dcm_filepath))
    else:
        # perform action
        if matched:
            if action.lower() == 'send_mail':
                send_mail_dcm(dcm_filepath, None, force, verbose)
            elif action.lower() == 'dcmpi_cli':
                io_dirs = (dirpath, '/SCR/TEMP')
                cmd = os.path.dirname(__file__) + \
                      '/dcmpi_run_cli.py -i {} -o {}'.format(*io_dirs)
                subprocess.call(cmd, shell=True)
            elif action.lower() == 'email+preprocess':
                send_mail_dcm(dcm_filepath, None, force, verbose)
                io_dirs = (dirpath, '/SCR/TEMP')
                cmd = os.path.dirname(__file__) + \
                      '/dcmpi_run_cli.py -i {} -o {}'.format(*io_dirs)
                subprocess.call(cmd, shell=True)
            else:
                msg('W: Action `{}` not valid.'.format(action))
        else:
            msg('I: Match `{}` was not successful.'.format(match))


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
        '-d', '--dirpath', metavar='DIR',
        default='.',
        help='set working directory [%(default)s]')
    arg_parser.add_argument(
        '-m', '--match', metavar='STR',
        default='{"_concat":"and","OperatorsName":"metere@cbs.mpg.de"}',
        help='set a match in the DICOM information [%(default)s]')
    arg_parser.add_argument(
        '-a', '--action', metavar='STR',
        default='email+preprocess',
        help='set action to perform [%(default)s]')
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

    dcm_analyze_dir(
        args.dirpath, args.match, args.action,
        args.force, args.verbose)

    exec_time = datetime.datetime.now() - begin_time
    msg('ExecTime: {}'.format(exec_time), args.verbose, VERB_LVL['debug'])


# ======================================================================
if __name__ == '__main__':
    main()
