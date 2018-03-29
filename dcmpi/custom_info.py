# !/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DCMPI: Instructions to extract information from DICOM using pydicom.
"""

# ======================================================================
# :: Future Imports
from __future__ import (
    division, absolute_import, print_function, unicode_literals)


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
import dcmpi.utils as utl

# from dcmpi_cli import INFO, DIRS
# from dcmpi_cli import VERB_LVL
# from dcmpi_cli import D_VERB_LVL


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
        '0x10': 8 / 8,
    },
    'pat_mode': {
        '0x1': 'None',
        '0x2': 'GRAPPA',
        '0x4': 'SENSE',
    },
    'coil_combine_mode': {
        '0x1': 'Adaptive',
        '0x2': 'SumOfSquares',
    },
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
        lambda x, p: time.strftime(p, utl.get_date(x)), '%Y-%m-%d'),
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
        (0x0040, 0x0254), lambda x, p: x.replace('^', '/'), None),
        # (0x0008, 0x1030), lambda x, p: x.replace('^', '/'), None),
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
        (0x0008, 0x1010), lambda x, p: p[x] if x in p else x, utl.STATION),
    'StationID': (
        (0x0008, 0x1010), None, None),
    'MagneticFieldStrength': (
        (0x0018, 0x0087), lambda x, p: '{}'.format(x), None),
    'NominalMagneticFieldStrength': (
        (0x0018, 0x0087),
        lambda x, p: '{}'.format(utl._nominal_B0(x)), None),
    'BeginDate': (
        (0x0008, 0x0020),
        lambda x, p: time.strftime(p, utl.get_date(x)),
        '%Y-%m-%d'),
    'BeginTime': (
        (0x0008, 0x0030),
        lambda x, p: time.strftime(p, utl.get_time(x)),
        '%H:%M:%S'),
    'EndDate': (
        (0x0008, 0x0023),
        lambda x, p: time.strftime(p, utl.get_date(x)),
        '%Y-%m-%d'),
    'EndTime': (
        (0x0008, 0x0033),
        lambda x, p: time.strftime(p, utl.get_time(x)),
        '%H:%M:%S'),
    'CoilSystem': (  # multiple replace
        (0x0051, 0x100f), lambda x, p: p[x] if x in p else x, COIL),
}

# ======================================================================
# :: Acquisition-specific information to be extracted
ACQUISITION = {
    'AcquisitionTime': (
        (0x0051, 0x100a), lambda x, p: utl.get_duration(x), None),
    'BeginDate': (
        (0x0008, 0x0022),
        lambda x, p: time.strftime(p, utl.get_date(x)),
        '%Y-%m-%d'),
    'BeginTime': (
        (0x0008, 0x0032),
        lambda x, p: time.strftime(p, utl.get_time(x)),
        '%H:%M:%S'),
    'EndDate': (
        (0x0008, 0x0023),
        lambda x, p: time.strftime(p, utl.get_date(x)),
        '%Y-%m-%d'),
    'EndTime': (
        (0x0008, 0x0033),
        lambda x, p: time.strftime(p, utl.get_time(x)),
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
def get_sequence_info(info, prot):
    """
    Information to extract based on protocol.

    Args:
        info (dict): information extracted from the DICOM headers
        prot (dict): information extracted from the acquisition protocol

    Returns:
        seq_bot (dict): instruction for sequence information extraction
    """
    seq_bot = {

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
            # :: Positioning (set_center and rotation angles)
            # todo: fix for correct interpretation in terms of angles
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
                lambda x, p: p[x] if x in p else x, SIEMENS_PROT['pat_mode']),
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
                prot['lContrasts'] if 'lContrasts' in prot else None),
            # :: TR
            'RepetitionTime::ms': (
                'alTR[]', lambda x, p: [n[1] * 1e-3 for n in x], None),
            # :: BW
            'BandWidth::Hz/px': (
                'sRXSPEC.alDwellTime[]',
                lambda x, p: [int(round(1 / (2 * p[1] * n[1] * 1e-9), -1))
                              for n in x[:p[0]]], (
                    prot['lContrasts']
                    if 'lContrasts' in prot else None,
                    prot['sKSpace.lBaseResolution']
                    if 'sKSpace.lBaseResolution' in prot else None)),
            # :: Dwell Time
            'DwellTime::ns': (
                'sRXSPEC.alDwellTime[]',
                lambda x, p: [n[1] for n in x[:p]],
                prot['lContrasts'] if 'lContrasts' in prot else None),
            # :: Coil Combine Mode
            'CoilCombineMode': (
                'ucCoilCombineMode',
                lambda x, p: p[x] if x in p else x,
                SIEMENS_PROT['coil_combine_mode']),
            # :: WiP parameters (useful for DEBUG)
            # 'WipD': ('sWiPMemBlock.adFree[]', None, None),
            # 'WipL': ('sWiPMemBlock.alFree[]', None, None),
        },

        # :: Phoenix ZIP Report
        'phoenix_zip_report': {}
    }

    # :: FLASH
    seq_bot['flash'] = {
        key: val for key, val in seq_bot['generic'].items()}
    seq_bot['flash'].update({})

    # :: MP2RAGE
    seq_bot['mp2rage'] = {
        key: val for key, val in seq_bot['generic'].items()}
    seq_bot['mp2rage'].update({
        # :: TI
        'InversionTime::ms': (
            'alTI[]', lambda x, p: [n[1] * 1e-3 for n in x], None),
        # :: TR_GRE
        'RepetitionTimeBlock::ms': (
            'lContrasts',
            lambda x, p: round(p[0][x - 1][1] * 1e-3 + 2 * p[1] *
                               p[2][x - 1][1] * 1e-6, 2),
            (
                prot['alTE[]'] if 'alTE[]' in prot else None,
                prot['sKSpace.lBaseResolution']
                if 'sKSpace.lBaseResolution' in prot else None,
                prot['sRXSPEC.alDwellTime[]']
                if 'sRXSPEC.alDwellTime[]' in prot else None)),
        # :: k-space coverage
        'UsePhaseInBlock': (
            'sWiPMemBlock.alFree[]',
            lambda x, p: True if x[2][1] == 1 else False, None),
    })

    # :: MT FLASH (Sam Hurley)
    # sWiPMemBlock.alFree[0]                   = 800  <- MT flip
    # sWiPMemBlock.alFree[1]                   = 17783 <- MT offset
    # sWiPMemBlock.alFree[2]                   = 20000 <- MT pulse duration
    # sWiPMemBlock.adFree[3]                   = 169 <- RF spoiling increment
    # sWiPMemBlock.adFree[4]                   = 1.8 <-FFT scale factor
    # sWiPMemBlock.adFree[5]                   = 10 <- SS grad spoiler moment
    # sWiPMemBlock.adFree[6]                   = 10 <- RO grad spoiler moment
    seq_bot['mt_flash_sah'] = {
        key: val for key, val in seq_bot['generic'].items()}
    seq_bot['mt_flash_sah'].update({
        'MtPulseCarrierFreq::Hz': (
            'sTXSPEC.asNucleusInfo[].lFrequency',
            lambda x, p: x[0][1], None),
        'MtPulseFlipAngle::deg': (
            'sWiPMemBlock.alFree[]',
            lambda x, p: x[0][1] if len(p) > 2 else None,
            prot['sWiPMemBlock.alFree[]'] if 'sWiPMemBlock.alFree[]' in prot
            else None),
        'MtPulseFreqOffset::Hz': (
            'sWiPMemBlock.alFree[]',
            lambda x, p: x[1][1] if len(p) > 2 else None,
            prot['sWiPMemBlock.alFree[]'] if 'sWiPMemBlock.alFree[]' in prot
            else None),
        'MtPulseDuration::ms': (
            'sWiPMemBlock.alFree[]',
            lambda x, p: x[2][1] * 1e-3 if len(p) > 2 else None,
            prot['sWiPMemBlock.alFree[]'] if 'sWiPMemBlock.alFree[]' in prot
            else None),
        'MtPulseSpoilingParameters': (
            'sWiPMemBlock.adFree[]',
            lambda x, p: [x[i][1] for i in (0, 2, 3)] if len(p) > 2 else None,
            prot['sWiPMemBlock.alFree[]'] if 'sWiPMemBlock.alFree[]' in prot
            else None),
        'FftScaleFactor': (
            'sWipMemBlock.adFree[]',
            lambda x, p: x[0][1] if len(p) > 2 else None,
            prot['sWiPMemBlock.alFree[]'] if 'sWiPMemBlock.alFree[]' in prot
            else None),
    })
    seq_id = identify_sequence(info, prot)
    if seq_id not in seq_bot:
        seq_id = 'generic'
    return seq_bot[seq_id]


# ======================================================================
def identify_sequence(info, prot):
    """
    Identify a sequence based on DICOM and protocol information

    Args:
        info (dict): information extracted from the DICOM headers
        prot (dict): information extracted from the acquisition protocol

    Returns:
        seq_id (str): sequence identifier
    """
    sequences_dict = {
        'phoenix_zip_report':
            (info['ProtocolName'] == 'Phoenix Document'),
        'flash':
            (prot and 'as_gre' in prot['tSequenceFileName']),
        'mp2rage':
            (prot and 'mp2rage' in prot['tSequenceFileName']),
        'mt_flash_sah':
            (prot and 'sah_gre_qmri' in prot['tSequenceFileName']),
        'afi_nw':
            (prot and 'nw_b1map3d' in prot['tSequenceFileName']),
    }

    seq_id = 'none' if not prot else 'generic'
    for tmp_seq_id in sorted(sequences_dict.keys()):
        match = sequences_dict[tmp_seq_id]
        # print(prot['tSequenceFileName'])
        if match:
            seq_id = tmp_seq_id
            break
    return seq_id


# ======================================================================
if __name__ == '__main__':
    print(__doc__)
