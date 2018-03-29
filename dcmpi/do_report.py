#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Create a report of the acquisitions from imaged data.
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
# import re  # Regular expression operations
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
# import pydicom as pydcm  # PyDicom (Read, modify and write DICOM files.)

# :: External Imports Submodules
# import matplotlib.pyplot as plt  # Matplotlib's pyplot: MATLAB-like syntax
# import mayavi.mlab as mlab  # Mayavi's mlab: MATLAB-like syntax
# import scipy.optimize  # SciPy: Optimization Algorithms
# import scipy.integrate  # SciPy: Integrations facilities
# import scipy.constants  # SciPy: Mathematal and Physical Constants
# import scipy.ndimage  # SciPy: ND-image Manipulation

# :: Local Imports
import dcmpi.utils as utl
from dcmpi import INFO, DIRS
from dcmpi import VERB_LVL, D_VERB_LVL, VERB_LVL_NAMES
from dcmpi import msg, dbg


# ======================================================================
def get_session(dirpath, summary):
    fields = (
        ('PatientName',
         lambda t: t[:4] if (t[3] == 'T' or t[3] == 'X') else t),
        ('BeginDate',
         lambda t: time.strftime('%Y-%m-%d', time.strptime(t, '%Y-%m-%d'))),
        ('BeginTime',
         lambda t: time.strftime('%H-%M', time.strptime(t, '%H:%M:%S'))),
        ('StationName',
         lambda t: utl.STATION[t] if t in utl.STATION else t),
        ('StudyDescription',
         lambda t: t),
    )
    try:
        subdirs = dirpath.split(os.sep)
        sample_id, study_id = subdirs[-2:-4:-1]
    except:
        info = []
        for key, func in fields:
            info.append(func(summary[key]))

        sample_id = utl.INFO_SEP.join(info[:-1])
        study_id = info[-1]
    finally:
        result = '{} / {}'.format(sample_id, study_id)
    return result


# ======================================================================
def html_input(typ, opt_str=''):
    opt_html = ''
    if opt_str:
        try:
            opts = json.loads(opt_str)
            for key, val in opts.items():
                opt_html += ' {}="{}"'.format(key, val)
        except:
            opt_html = opt_str
    output = '<input type="{}"{} />'.format(typ, opt_html)
    return output


# ======================================================================
def check_box(key, info):
    return html_input(
        'checkbox', ('checked' if key in info and info[key] == True else ''))


# ======================================================================
def sort_param(arg):
    key, val = arg
    order = (
        'Sequence',
        'TransmitCoil', 'ReceiveCoil',
        'FieldOfView[ROxPExSL]::mm',
        'MatrixSize[ROxPExSL]::px', 'MatrixSizeOverSlice::px',
        'Position',
        'NumAverages',
        'PAT', 'PartialFourier',
    )
    idx = order.index(key) if key in order else len(order) + 1
    return idx, key, val


# ======================================================================
def get_param(acq):
    mask = ('ProtocolName', 'BeginDate', 'BeginTime', 'EndDate', 'EndTime',
            'AcquisitionTime', 'Duration', 'ExpectedScanTime::sec',
            'SequenceName',
            'DwellTime::ns')

    mask_filter = (
        (lambda x: 'Sequence' not in x),
        (lambda x: 'FieldOfView' not in x),
        (lambda x: 'MatrixSize' not in x),
        (lambda x: 'AngleNormalTo' not in x),
        (lambda x: 'CenterPosition' not in x),
        (lambda x: 'ParallelAcquisitionTechnique' not in x),
        (lambda x: 'PartialFourier' not in x),
    )

    report = {}
    # :: add specially grouped fields
    # sequence identifier
    seq_params = (
        'SequenceCode', 'SequenceVariant', 'SequenceFileName', 'SequenceName')
    report['Sequence'] = json.dumps([acq[key] for key in seq_params])
    # field of view
    report['FieldOfView[ROxPExSL]::mm'] = json.dumps((
        acq['FieldOfViewReadOut::mm'], acq['FieldOfViewPhase::mm'],
        acq['FieldOfViewSlice::mm']))
    # matrix size
    report['MatrixSize[ROxPExSL]::px'] = json.dumps((
        acq['MatrixSizeReadOut::px'], acq['MatrixSizePhase::px'],
        acq['MatrixSizeSlice::px']))
    if acq['MatrixSizeOverSlice::px'] > acq['MatrixSizeSlice::px']:
        report['MatrixSizeOverSlice::px'] = json.dumps(
            acq['MatrixSizeOverSlice::px'])
    # position information
    pos_params = (
        'CenterPositionCoronal::mm', 'CenterPositionSagittal::mm',
        'CenterPositionTransverse::mm', 'AngleNormalToSagittal::deg',
        'AngleNormalToCoronal::deg', 'AngleNormalToTransverse::deg')
    report['Position'] = json.dumps([acq[key] for key in pos_params])
    # parallel acquisition technique
    pat_params = (
        'ParallelAcquisitionTechniqueMode',
        'ParallelAcquisitionTechniqueAccelerationPhase',
        'ParallelAcquisitionTechniqueAccelerationSlice')
    report['PAT'] = json.dumps([acq[key] for key in pat_params])
    # partial Fourier
    pf_params = (
        'PartialFourierPhase',
        'PartialFourierSlice')
    report['PartialFourier'] = json.dumps(
        ['{}/{}'.format(int(acq[key] * 8), 8) for key in pf_params])

    for key, val in acq.items():
        if key not in mask and all([test(key) for test in mask_filter]) and \
                        val != None and val != 'N/A':
            report[key] = json.dumps(val)
    return report


# ======================================================================
def do_report(
        in_dirpath,
        out_dirpath,
        basename='{name}_{date}_{time}_{sys}',
        method='pydicom',
        file_format='pdf',
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
    file_format : str (optional)
        | Output format. HTML will always be present. Accepted values:
        * pydicom: Use PyDICOM Python module.
    force : boolean (optional)
        Force new processing.
    verbose : int (optional)
        Set level of verbosity.

    Returns
    =======
    None.

    """
    msg(':: Creating HTML and PDF report...')
    msg('Input:  {}'.format(in_dirpath))
    msg('Output: {}'.format(out_dirpath))

    dcm_filename, compression = utl.find_a_dicom(in_dirpath)
    out_basename = utl.fill_from_dicom(basename, dcm_filename)
    html_basename = out_basename + '.html'
    msg('HTML: {}'.format(html_basename))
    out_filepath = os.path.join(out_dirpath, html_basename)

    # proceed only if output is not likely to be there
    if not os.path.exists(out_filepath) or force:
        # :: create output directory if not exists and extract images
        if not os.path.exists(out_dirpath):
            os.makedirs(out_dirpath)

        # :: get information
        summary, extra = {}, {}
        acquisitions = []
        if method == 'pydicom':
            # :: create temporary info data
            from dcmpi.get_info import get_info
            info_dirpath = os.path.join(
                os.path.dirname(in_dirpath), utl.ID['info'])
            get_info(
                in_dirpath, info_dirpath, method, force=force, verbose=verbose)
            for name in sorted(os.listdir(info_dirpath)):
                target = os.path.join(info_dirpath, name)
                with open(target, 'r') as target_file:
                    if name.startswith('summary.info'):
                        summary = json.load(target_file)
                    elif name.startswith('extra.info'):
                        extra = json.load(target_file)
                    elif name.startswith('a'):
                        acquisitions.append((
                            name[:name.find(utl.INFO_SEP)],
                            json.load(target_file)))

        else:
            msg('W: Unknown method `{}`.'.format(method))

        # :: create report
        tpl_dirpath = os.path.join(
            os.path.dirname(__file__), 'report_templates')

        if summary and acquisitions and os.path.isdir(tpl_dirpath):
            # :: always create HTML report
            # import templates
            template = {
                'report': 'report_template.html',
                'acq': 'acquisition_template.html',
                'acq_param': 'acquisition_parameter_template.html',
            }
            for key, filename in template.items():
                tpl_filepath = os.path.join(tpl_dirpath, filename)
                with open(tpl_filepath, 'r') as tpl_file:
                    template[key] = tpl_file.read()
            # replace tags
            acq_html = ''
            for n_acq, acq in acquisitions:
                acq_param_html = ''
                for key, val in sorted(get_param(acq).items(), key=sort_param):
                    acq_param_html += template['acq_param'].replace(
                        '[ACQ-PARAM-KEY]', key).replace(
                        '[ACQ-PARAM-VAL]', val)
                tags = {
                    '[ACQ-ID]': n_acq,
                    '[ACQ-TIME]': acq['AcquisitionTime'],
                    '[ACQ-PROTOCOL]': acq['ProtocolName'],
                    '[ACQ-SERIES]':
                        ', '.join([series[:series.find(utl.INFO_SEP)]
                                   for series in acq['_series']]),
                    '[ACQUISITION-PARAMETER-TEMPLATE]': acq_param_html,
                }
                tmp_acq_html = template['acq']
                for tag, val in tags.items():
                    tmp_acq_html = tmp_acq_html.replace(tag, val)
                acq_html += tmp_acq_html
            report_html = template['report']
            tags = {
                '[TIMESTAMP]': time.strftime('%c UTC', time.gmtime()),
                '[SESSION-INFO]': get_session(info_dirpath, summary),
                '[CUSTOM-PIL]':
                    extra['pil'] if 'pil' in extra else \
                        html_input('text', '{"maxlength": 4}'),
                '[CUSTOM-U-ID]':
                    extra['uid'] if 'uid' in extra else \
                        html_input('text', '{"maxlength": 12}'),
                '[CUSTOM-B-ID]':
                    extra['bid'] if 'bid' in extra else \
                        html_input('text', '{"maxlength": 4}'),
                '[CUSTOM-NUM-7T]':
                    extra['pil'] if 'pil' in extra else \
                        html_input('text', '{"maxlength": 3}'),
                '[PATIENT-NAME]': summary['PatientName'],
                '[PATIENT-ID]': summary['PatientID'],
                '[PATIENT-SEX]': summary['PatientSex'],
                '[PATIENT-AGE]': summary['PatientAge'],
                '[PATIENT-BIRTH-DATE]': summary['PatientBirthDate'],
                '[PATIENT-WEIGHT]': summary['PatientWeight'],
                '[PATIENT-HEIGHT]': summary['PatientHeight'],
                '[MAGNETIC-FIELD-STRENGTH]':
                    summary['NominalMagneticFieldStrength'],
                '[SYSTEM-NAME]': summary['StationName'],
                '[SYSTEM-ID]': summary['StationID'],
                '[LOCATION]': summary['InstitutionName'],
                '[COIL-SYSTEM]': summary['CoilSystem'],
                '[EARPHONES]': check_box('Earphones', extra),
                '[PADS]': check_box('Pads', extra),
                '[PULSE-OXIMETER]': check_box('PulseOximeter', extra),
                '[PROJECTOR]': check_box('Projector', extra),
                '[EXT-COMPUTER]': check_box('ExtComputer', extra),
                '[PARALLEL-TX]': check_box('ParallelTX', extra),
                '[OTHERS]':
                    (extra['Others'] if 'Others' in extra and extra['Others'] \
                         else html_input('text')) + html_input('text'),
                '[STUDY-NAME]': html_input('text', '{"maxlength": 16}'),
                '[STUDY-ID]': html_input('text', '{"maxlength": 16}'),
                '[STUDY-DESCR]': summary['StudyDescription'],
                '[BEGIN-DATE]': summary['BeginDate'],
                '[BEGIN-TIME]': summary['BeginTime'],
                '[END-DATE]': summary['EndDate'],
                '[END-TIME]': summary['EndTime'],
                '[DURATION]': summary['Duration'],
                '[PERFORMER]': summary['Performer'],
                '[OPERATOR]': summary['Operator'],
                '[ACQUISITION-TEMPLATE]': acq_html
            }
            for tag, val in tags.items():
                if val == 'N/A':
                    val = ''
                report_html = report_html.replace(tag, val)
            # todo: improve filename (e.g. from upper folder or recalculate)

            with open(out_filepath, 'w') as html_file:
                html_file.write(report_html)

            if file_format == 'pdf':
                pdf_filename = out_basename + '.pdf'
                msg('Report: {}'.format(pdf_filename))
                pdf_filepath = os.path.join(out_dirpath, pdf_filename)
                opts = (
                    ' --page-size {}'.format('A4'),
                    ' --margin-bottom {}'.format('15mm'),
                    ' --margin-left {}'.format('15mm'),
                    ' --margin-right {}'.format('15mm'),
                    ' --margin-top {}'.format('15mm'),
                    # ' --no-pdf-compression',  # n/a in Ubuntu 14.04
                )
                cmd = 'wkhtmltopdf {} {} {}'.format(
                    ' '.join(opts), out_filepath, pdf_filepath)
                ret_val, p_stdout, p_stderr = utl.execute(cmd, verbose=verbose)

            else:
                msg('W: Unknown format `{}`.'.format(file_format))

        else:
            msg('W: Acquisition information not found.')


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
        '-b', '--basename', metavar='NAME',
        default='{name}_{date}_{time}_{sys}',
        help='set output directory [%(default)s]')
    arg_parser.add_argument(
        '-m', '--method', metavar='METHOD',
        default='pydicom',
        help='set extraction method [%(default)s]')
    arg_parser.add_argument(
        '-a', '--file_format', metavar='METHOD',
        default='pdf',
        help='set output format [%(default)s]')
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

    do_report(
        args.in_dirpath, args.out_dirpath,
        args.basename,
        args.method, args.file_format,
        args.force, args.verbose)

    exec_time = datetime.datetime.now() - begin_time
    msg('ExecTime: {}'.format(exec_time), args.verbose, VERB_LVL['debug'])


# ======================================================================
if __name__ == '__main__':
    main()
