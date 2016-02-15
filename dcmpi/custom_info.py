# !/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Instructions to extract information from DICOM using pydicom.
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
# from __future__ import unicode_literals


# ======================================================================
# :: Python Standard Library Imports
# import os  # Miscellaneous operating system interfaces
# import shutil  # High-level file operations
# import math  # Mathematical functions
import time  # Time access and conversions
# import datetime  # Basic date and time types
# import operator  # Standard operators as functions
# import collections  # High-performance container datatypes
# import argparse  # Parser for command-line options, arguments and subcommands
# import itertools  # Functions creating iterators for efficient looping
import functools  # Higher-order functions and operations on callable objects
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
import dcmpi.common as dcmlib

# from dcmpi import INFO
# from dcmpi import VERB_LVL
# from dcmpi import D_VERB_LVL


# ======================================================================
# :: receive coil name look-up table
COIL = {
    'C:A32': 'Nova TX:CP / RX:32 Ch.',
    'C:A24': 'Nova TX:CP / RX:24 Ch.'
}

# ======================================================================
# :: Siemens's protocol's parameters look-up table
SIEMENS_PROT = {
    'partial_fourier': {
        '0x1': 4 / 8,
        '0x2': 5 / 8,
        '0x4': 6 / 8,
        '0x8': 7 / 8,
        '0x10': 8 / 8},
    'pat_mode': {
        '0x1': 'None',
        '0x2': 'GRAPPA',
        '0x4': 'SENSE',},
}

# ======================================================================
# :: Generic session information to be extracted
SESSION = {
    'PatientName': (
        (0x0010, 0x0010), None, None),
    'PatientID': (
        (0x0010, 0x0020), None, None),
    'PatientBirthDate': (  # reformat
        (0x0010, 0x0030),
        lambda x, p: time.strftime(p, dcmlib.get_date(x)), '%Y-%m-%d'),
    'PatientAge': (  # reformat
        (0x0010, 0x1010), lambda x, p: str(int(str(x)[:-1])) + ' yr', None),
    'PatientSex': (  # reformat
        (0x0010, 0x0040), lambda x, p: x.lower(), None),
    'PatientWeight': (  # reformat
        (0x0010, 0x1030), lambda x, p: str(x) + ' kg', None),
    'PatientHeight': (  # reformat
        (0x0010, 0x1020), lambda x, p: str(x) + ' m', None),
    'PatientComment': (
        (0x0010, 0x4000), lambda x, p: str(x), None),
    'StudyDescription': (
        (0x0008, 0x1030), lambda x, p: x.replace('^', '/'), None),
    'Performer': (
        (0x0008, 0x1050), None, None),
    'Operator': (
        (0x0008, 0x1070), None, None),
    'Reference': (
        (0x0008, 0x0090), None, None),
    'InstitutionName': (
        (0x0008, 0x0080), None, None),
    'InstitutionAddress': (
        (0x0008, 0x0081),  # multiple replace
        lambda x, p: functools.reduce(lambda a, kv: a.replace(*kv), p, x),
        ((',', ', '),)),
    'StationName': (
        (0x0008, 0x1010), lambda x, p: p[x] if x in p else x, dcmlib.STATION),
    'StationID': (
        (0x0008, 0x1010), None, None),
    'MagneticFieldStrength': (
        (0x0018, 0x0087), lambda x, p: '{}'.format(x), None),
    'NominalMagneticFieldStrength': (
        (0x0018, 0x0087),
        lambda x, p: '{}'.format(dcmlib._nominal_B0(x)), None),
    'BeginDate': (
        (0x0008, 0x0020),
        lambda x, p: time.strftime(p, dcmlib.get_date(x)),
        '%Y-%m-%d'),
    'BeginTime': (
        (0x0008, 0x0030),
        lambda x, p: time.strftime(p, dcmlib.get_time(x)),
        '%H:%M:%S'),
    'EndDate': (
        (0x0008, 0x0023),
        lambda x, p: time.strftime(p, dcmlib.get_date(x)),
        '%Y-%m-%d'),
    'EndTime': (
        (0x0008, 0x0033),
        lambda x, p: time.strftime(p, dcmlib.get_time(x)),
        '%H:%M:%S'),
    'CoilSystem': (  # multiple replace
        (0x0051, 0x100f), lambda x, p: p[x] if x in p else x, COIL),
}

# ======================================================================
# :: Acquisition-specific information to be extracted
ACQUISITION = {
    'AcquisitionTime': (
        (0x0051, 0x100a), lambda x, p: dcmlib.get_duration(x), None),
    'BeginDate': (
        (0x0008, 0x0022),
        lambda x, p: time.strftime(p, dcmlib.get_date(x)),
        '%Y-%m-%d'),
    'BeginTime': (
        (0x0008, 0x0032),
        lambda x, p: time.strftime(p, dcmlib.get_time(x)),
        '%H:%M:%S'),
    'EndDate': (
        (0x0008, 0x0023),
        lambda x, p: time.strftime(p, dcmlib.get_date(x)),
        '%Y-%m-%d'),
    'EndTime': (
        (0x0008, 0x0033),
        lambda x, p: time.strftime(p, dcmlib.get_time(x)),
        '%H:%M:%S'),
    'TransmitCoil': (
        (0x0018, 0x1251), None, None),
    'ReceiveCoil': (  # look-up table
        (0x0051, 0x100f), None, None),
    'SequenceCode': (
        (0x0018, 0x0020), None, None),
    'SequenceVariant': (
        (0x0018, 0x0021), None, None),
    'SequenceName': (
        (0x0018, 0x0024), None, None),
    'ProtocolName': (
        (0x0018, 0x1030), None, None),
}

# ======================================================================
# :: Serie-specific information to be extracted
SERIES = {
}


# ======================================================================
def get_sequence_info(info_dict, prot_dict):
    """
    Information to extract based on protocol.
    """
    sequence_dict = {

        # :: NO SEQUENCE!!!
        'none': {},

        # :: GENERIC
        'generic': {
            # :: sequence file name
            'SequenceFileName': (
                'tSequenceFileName', None, None),
            # :: acquisition time
            'ExpectedScanTime::sec': (
                'lTotalScanTimeSec', None, None),
            # :: matrix sizes
            'MatrixSizeReadOut::px': (
                'sKSpace.lBaseResolution', None, None),
            'MatrixSizePhase::px': (
                'sKSpace.lPhaseEncodingLines', None, None),
            'MatrixSizeSlice::px': (
                'sKSpace.lImagesPerSlab', None, None),
            'MatrixSizeOverSlice::px': (
                'sKSpace.lPartitions', None, None),
            # :: FOV
            'FieldOfViewReadOut::mm': (
                'sSliceArray.asSlice[].dReadoutFOV',
                lambda x, p: [n[1] for n in x], None),
            'FieldOfViewPhase::mm': (
                'sSliceArray.asSlice[].dPhaseFOV',
                lambda x, p: [n[1] for n in x], None),
            'FieldOfViewSlice::mm': (
                'sSliceArray.asSlice[].dThickness',
                lambda x, p: [n[1] for n in x], None),
            # :: resolution  # TODO?
            #        'FieldOfViewReadOut::mm': (
            #            'sSliceArray.asSlice[].dReadoutFOV',
            #            lambda x, p: [n[1] for n in x], None),
            #        'FieldOfViewPhase::mm': (
            #            'sSliceArray.asSlice[].dPhaseFOV',
            #            lambda x, p: [n[1] for n in x], None),
            #        'FieldOfViewSlice::mm': (
            #            'sSliceArray.asSlice[].dThickness',
            #            lambda x, p: [n[1] for n in x], None),
            # :: Positioning (center and rotation angles)
            'CenterPositionSagittal::mm': (
                'sSliceArray.asSlice[].sPosition.dSag',
                lambda x, p: [n[1] for n in x], None),
            'CenterPositionCoronal::mm': (
                'sSliceArray.asSlice[].sPosition.dCor',
                lambda x, p: [n[1] for n in x], None),
            'CenterPositionTransverse::mm': (
                'sSliceArray.asSlice[].sPosition.dTra',
                lambda x, p: [n[1] for n in x], None),
            'AngleNormalToSagittal::deg': (
                'sSliceArray.asSlice[].sNormal.dSag',
                lambda x, p: [n[1] for n in x], None),
            'AngleNormalToCoronal::deg': (
                'sSliceArray.asSlice[].sNormal.dCor',
                lambda x, p: [n[1] for n in x], None),
            'AngleNormalToTransverse::deg': (
                'sSliceArray.asSlice[].sNormal.dTra',
                lambda x, p: [n[1] for n in x], None),
            # :: Partial Fourier factors
            'PartialFourierPhase': (
                'sKSpace.ucPhasePartialFourier',
                lambda x, p: p[x] if x in p else x,
                SIEMENS_PROT['partial_fourier']),
            'PartialFourierSlice': (
                'sKSpace.ucSlicePartialFourier',
                lambda x, p: p[x] if x in p else x,
                SIEMENS_PROT['partial_fourier']),
            # :: Parallel Acquisition Technique (PAT)
            'ParallelAcquisitionTechniqueMode': (
                'sPat.ucPATMode',
                lambda x, p: p[x] if x in p else x,
                SIEMENS_PROT['pat_mode']),
            'ParallelAcquisitionTechniqueAccelerationPhase': (
                'sPat.lAccelFactPE', None, None),
            'ParallelAcquisitionTechniqueAccelerationSlice': (
                'sPat.lAccelFact3D', None, None),
            'ParallelAcquisitionTechniqueReferenceLinesPhase': (
                'sPat.lRefLinesPE', None, None),
            # :: Averages
            'NumAverages': (
                'lAverages', None, None),
            # :: FA
            'FlipAngle::deg': (
                'adFlipAngleDegree[]', lambda x, p: [n[1] for n in x], None),
            # :: TE
            'NumEchoes': ('lContrasts', None, None),
            'EchoTime::ms': (
                'alTE[]', lambda x, p: [n[1] * 1e-3 for n in x[:p]],
                prot_dict['lContrasts'] if 'lContrasts' in prot_dict else None),
            # :: TR
            'RepetitionTime::ms': (
                'alTR[]', lambda x, p: [n[1] * 1e-3 for n in x], None),
            # :: BW
            'BandWidth::Hz/px': (
                'sRXSPEC.alDwellTime[]',
                lambda x, p: [int(round(1 / (2 * p[1] * n[1] * 1e-9), -1))
                              for n in x[:p[0]]], (
                    prot_dict[
                        'lContrasts'] if 'lContrasts' in prot_dict else None,
                    prot_dict['sKSpace.lBaseResolution']
                    if 'sKSpace.lBaseResolution' in prot_dict else None)),
            # :: Dwell Time
            'DwellTime::ns': (
                'sRXSPEC.alDwellTime[]',
                lambda x, p: [n[1] for n in x[:p]],
                prot_dict['lContrasts'] if 'lContrasts' in prot_dict else None),
        },

        # :: Phoenix ZIP Report
        'phoenix_zip_report': {}
    }

    # :: FLASH
    sequence_dict['flash'] = {key: val for key, val in
                              sequence_dict['generic'].items()}
    sequence_dict['flash'].update({})

    # :: MP2RAGE
    sequence_dict['mp2rage'] = {key: val for key, val in
                                sequence_dict['generic'].items()}
    sequence_dict['mp2rage'].update({
        # :: TI
        'InversionTime::ms': (
            'alTI[]', lambda x, p: [n[1] * 1e-3 for n in x], None),
        # :: TR_GRE
        'RepetitionTimeBlock::ms': (
            'lContrasts',
            lambda x, p: round(p[0][x - 1][1] * 1e-3 + 2 * p[1] *
                               p[2][x - 1][1] * 1e-6, 2),
            (
                prot_dict['alTE[]'] if 'alTE[]' in prot_dict else None,
                prot_dict['sKSpace.lBaseResolution']
                if 'sKSpace.lBaseResolution' in prot_dict else None,
                prot_dict['sRXSPEC.alDwellTime[]']
                if 'sRXSPEC.alDwellTime[]' in prot_dict else None)),
        # :: k-space coverage
        'UsePhaseInBlock': (
            'sWiPMemBlock.alFree[]',
            lambda x, p: True if x[2][1] == 1 else False, None),
    })

    return sequence_dict[identify_sequence(info_dict, prot_dict)]


# ======================================================================
def identify_sequence(info_dict, prot_dict):
    """
    Information to extract based on protocol.
    """
    sequences_dict = {
        'phoenix_zip_report':
            (info_dict['ProtocolName'] == 'Phoenix Document'),
        'flash':
            (prot_dict and
             prot_dict['tSequenceFileName'] == '%CustomerSeq%\\AS\\as_gre'),
        'mp2rage':
            (prot_dict and
             prot_dict[
                 'tSequenceFileName'] == '%CustomerSeq%\\mp2rage_wip602B'),
    }

    identified_sequence = 'none' if not prot_dict else 'generic'
    for seq_id in sorted(sequences_dict.iterkeys()):
        match = sequences_dict[seq_id]
        if match:
            identified_sequence = seq_id
            break
    return identified_sequence


# ======================================================================
if __name__ == '__main__':
    print(__doc__)
