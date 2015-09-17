#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Extract and preprocess DICOM files from a single session.
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
import sys  # System-specific parameters and functions
# import shutil  # High-level file operations
import platform  # Access to underlying platform’s identifying data
# import math  # Mathematical functions
import time  # Time access and conversions
import datetime  # Basic date and time types
# import re  # Regular expression operations
# import operator  # Standard operators as functions
# import collections  # High-performance container datatypes
# import argparse  # Parser for command-line options, arguments and subcommands
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
# import dicom as pydcm  # PyDicom (Read, modify and write DICOM files.)
# import PySide  # PySide (Python QT bindings)

# :: External Imports Submodules
# import matplotlib.pyplot as plt  # Matplotlib's pyplot: MATLAB-like syntax
# import mayavi.mlab as mlab  # Mayavi's mlab: MATLAB-like syntax
# import scipy.optimize  # SciPy: Optimization Algorithms
# import scipy.integrate  # SciPy: Integrations facilities
# import scipy.constants  # SciPy: Mathematal and Physical Constants
# import scipy.ndimage  # SciPy: ND-image Manipulation
# import PySide.QtCore  # PySide: Core module
import PySide.QtGui  # PySide GUI module

# :: Local Imports
# import mri_tools.lib.base as mrb
# import mri_tools.lib.utils as mru
# import mri_tools.lib.nifti as mrn
# import mri_tools.lib.geom_mask as mrgm
# import mri_tools.lib.mp2rage as mp2rage
from dcmpi.import_sources import import_sources
from dcmpi.sorting import sorting
from dcmpi.get_nifti import get_nifti
from dcmpi.get_prot import get_prot
from dcmpi.get_meta import get_meta
from dcmpi.get_info import get_info
from dcmpi.report import report
from dcmpi.backup import backup
import dcmpi.lib.common as dcmlib
# from dcmpi import INFO
from dcmpi import VERB_LVL
from dcmpi import D_VERB_LVL
# from dcmpi import _firstline


# ======================================================================
D_INPUT_DIR = '/scr/'
D_OUTPUT_DIR = '../../raw_data/siemens/'
#D_INPUT_DIR = '/scr/isar1/TEMP/SOURCE_DICOM'
#D_OUTPUT_DIR = '/scr/isar1/TEMP/OUTPUT_DICOM'
D_SUBPATH = '[study]/[name]_[date]_[time]_[sys]/dcm'


# ======================================================================
class Main(PySide.QtGui.QWidget):

    def __init__(self):
        super(Main, self).__init__()
        if len(sys.argv) > 1:
            self.base_cmd = sys.argv[1]
        else:
            self.base_cmd = ''
        self.server_list = [
            platform.node(),
            'hayd',
            'waters',
            'wehner',
            'horton',
            'lenin',
            'brenda',
            'carlos',
            'berg']
        self.actions = [
            ('import_sources', 'Import Sources', True, None),
            ('sorting', 'Sort DICOM', True, None),
            ('get_nifti', 'Get NIfTI images', True, dcmlib.ID['nifti']),
            ('get_meta', 'Get metadata', True, dcmlib.ID['meta']),
            ('get_prot', 'Get protocol', True, dcmlib.ID['prot']),
            ('get_info', 'Get information', True, dcmlib.ID['info']),
            ('report', 'Create Report', True, dcmlib.ID['report']),
            ('backup', 'Backup DICOM Sources', True, dcmlib.ID['backup']),
        ]
        self.options = [
            ('Force', bool, False, None),
            ('Verbosity', int, D_VERB_LVL,
                (VERB_LVL['none'], VERB_LVL['debug'])),
        ]
        self.initUI()

    # --------------------------------
    # :: initialize
    def initUI(self):
        # :: input
        self.lblInput = PySide.QtGui.QLabel('Input:', self)
        self.lstInput = PySide.QtGui.QListWidget(self)

        self.btnImport = PySide.QtGui.QPushButton('&Import')
        self.btnImport.setIcon(
            self.style().standardIcon(
            PySide.QtGui.QStyle.SP_DialogOpenButton))
        self.btnImport.clicked.connect(self.btnImport_onClicked)

        self.btnExport = PySide.QtGui.QPushButton('&Export')
        self.btnExport.setIcon(
            self.style().standardIcon(
            PySide.QtGui.QStyle.SP_DialogSaveButton))
        self.btnExport.clicked.connect(self.btnExport_onClicked)

        self.btnAdd = PySide.QtGui.QPushButton('&Add')
        self.btnAdd.setIcon(
            self.style().standardIcon(
            PySide.QtGui.QStyle.SP_DirIcon))
        self.btnAdd.clicked.connect(self.btnAdd_onClicked)

        self.btnRemove = PySide.QtGui.QPushButton('&Remove')
        self.btnRemove.setIcon(
            self.style().standardIcon(
            PySide.QtGui.QStyle.SP_TrashIcon))
        self.btnRemove.clicked.connect(self.btnRemove_onClicked)

        self.btnClear = PySide.QtGui.QPushButton('&Clear')
        self.btnClear.setIcon(
            self.style().standardIcon(
            PySide.QtGui.QStyle.SP_DialogResetButton))
        self.btnClear.clicked.connect(self.btnClear_onClicked)

        self.hboxButtonsInput = PySide.QtGui.QHBoxLayout()
        self.hboxButtonsInput.addWidget(self.btnImport)
        self.hboxButtonsInput.addWidget(self.btnExport)
        self.hboxButtonsInput.addStretch(1.0)
        self.hboxButtonsInput.addWidget(self.btnAdd)
        self.hboxButtonsInput.addWidget(self.btnRemove)
        self.hboxButtonsInput.addWidget(self.btnClear)

        self.vboxInput = PySide.QtGui.QVBoxLayout()
        self.vboxInput.addWidget(self.lblInput)
        self.vboxInput.addWidget(self.lstInput)
        self.vboxInput.addLayout(self.hboxButtonsInput)

        # :: output
        self.lblOutput = PySide.QtGui.QLabel('Output:', self)
        self.lblOutput.setMinimumWidth(60)
        out_dirpath = D_OUTPUT_DIR if os.path.isdir(D_OUTPUT_DIR) else '.'
        self.lneOutput = PySide.QtGui.QLineEdit(out_dirpath)
        self.lneOutput.setReadOnly(True)
        self.lneOutput.mousePressEvent = self.lneOutput_onClicked

        subpath_help = dcmlib.fill_from_dicom.__doc__
        subpath_help = subpath_help[
            subpath_help.find('format_str : string\n') +
            len('format_str : string\n'):
            subpath_help.find('\n    extra_fields : boolean')]
        subpath_help = subpath_help.replace('        | ', '')
        subpath_help = '\n'.join(subpath_help.split('\n')[1:])
        self.lblSubdir = PySide.QtGui.QLabel('Subpath:', self)
        self.lblSubdir.setMinimumWidth(60)
        self.lneSubpath = PySide.QtGui.QLineEdit(D_SUBPATH)
        self.lneSubpath.setToolTip(subpath_help)

        self.hboxOutput = PySide.QtGui.QHBoxLayout()
        self.hboxOutput.addWidget(self.lblOutput)
        self.hboxOutput.addWidget(self.lneOutput)

        self.hboxSubdir = PySide.QtGui.QHBoxLayout()
        self.hboxSubdir.addWidget(self.lblSubdir)
        self.hboxSubdir.addWidget(self.lneSubpath)

        self.vboxOutput = PySide.QtGui.QVBoxLayout()
        self.vboxOutput.addLayout(self.hboxOutput)
        self.vboxOutput.addLayout(self.hboxSubdir)

        self.vboxIO = PySide.QtGui.QVBoxLayout()
        self.vboxIO.addLayout(self.vboxInput)
        self.vboxIO.addLayout(self.vboxOutput)

        # :: actions
        self.lblActions = PySide.QtGui.QLabel('Actions:', self)
        self.chkActions = []
        for name, label, default, subdir in self.actions:
            checkbox = PySide.QtGui.QCheckBox(label, self)
            if default:
                checkbox.toggle()
            if name == 'import_sources':
                checkbox.stateChanged.connect(self.chkImport_stateChanged)
            checkbox.setToolTip('Warning: toggling actions is experimental.')
            self.chkActions.append(checkbox)

        self.vboxActions = PySide.QtGui.QVBoxLayout()
        self.vboxActions.addWidget(self.lblActions)
        for checkbox in self.chkActions:
            self.vboxActions.addWidget(checkbox)
        self.vboxActions.addStretch(1.0)

        self.chkImport_stateChanged()

        # :: options
        self.lblOptions = PySide.QtGui.QLabel('Options:', self)
        self.wdgtOptions = []
        for name, val_type, default, extra in self.options:
            if val_type == bool:
                widget = PySide.QtGui.QCheckBox(name, self)
                if default:
                    widget.checked()
                self.wdgtOptions.append((widget, None, None))
            elif val_type == int:
                label = PySide.QtGui.QLabel(name, self)
                widget = PySide.QtGui.QSpinBox(self)
                widget.setRange(extra[0], extra[1])
                widget.setValue(default)
                box = PySide.QtGui.QHBoxLayout()
                box.addWidget(label)
                box.addWidget(widget)
                self.wdgtOptions.append((widget, label, box))

        self.vboxOptions = PySide.QtGui.QVBoxLayout()
        self.vboxOptions.addWidget(self.lblOptions)
        for widget, label, box in self.wdgtOptions:
            if box:
                self.vboxOptions.addLayout(box)
            else:
                self.vboxOptions.addWidget(widget)
        self.vboxOptions.addStretch(1.0)

        self.vboxMore = PySide.QtGui.QVBoxLayout()
        self.vboxMore.addLayout(self.vboxActions)
        self.vboxMore.addLayout(self.vboxOptions)

        self.hboxIOAndMore = PySide.QtGui.QHBoxLayout()
        self.hboxIOAndMore.addLayout(self.vboxIO)
        self.hboxIOAndMore.addLayout(self.vboxMore)

        # :: choice of the server
        self.lblServer = PySide.QtGui.QLabel('Server:', self)
        self.cmbServer = PySide.QtGui.QComboBox(self)
        self.cmbServer.setEditable(True)
        for server in self.server_list:
            self.cmbServer.addItem(server)

        self.hboxServer = PySide.QtGui.QHBoxLayout()
        self.hboxServer.addStretch(1.0)
        self.hboxServer.addWidget(self.lblServer)
        self.hboxServer.addWidget(self.cmbServer)

        # :: buttons
        self.btnRun = PySide.QtGui.QPushButton('&Run')
        self.btnRun.setIcon(
            self.style().standardIcon(
            PySide.QtGui.QStyle.SP_DialogApplyButton))
        self.btnRun.clicked.connect(self.btnRun_onClicked)

        self.btnClose = PySide.QtGui.QPushButton('&Close')
        self.btnClose.setIcon(
            self.style().standardIcon(
            PySide.QtGui.QStyle.SP_DialogCloseButton))
        self.btnClose.clicked.connect(self.close)

        self.hboxButtons = PySide.QtGui.QHBoxLayout()
        self.hboxButtons.addStretch(1.0)
        self.hboxButtons.addWidget(self.btnRun)
        self.hboxButtons.addWidget(self.btnClose)

        # :: main
        self.vboxMain = PySide.QtGui.QVBoxLayout()
        self.vboxMain.addLayout(self.hboxIOAndMore)
        self.vboxMain.addLayout(self.hboxServer)
        self.vboxMain.addLayout(self.hboxButtons)

        self.setLayout(self.vboxMain)

        self.resize(720, 450)
        self.setWindowTitle('Extract and preprocess DICOM')
        self.setWindowIcon(
            self.style().standardIcon(
            PySide.QtGui.QStyle.SP_ComputerIcon))
        self.show()

    # --------------------------------
    # :: actions
    def btnRun_onClicked(self, event=None):
        # TODO: redirect stdout to log box
        # TODO: run as a separate process (eventually in parallel?)
        tot_begin = time.time()
        # extract options
        force = self.wdgtOptions[0][0].isChecked()
        print('Force:\t{}'.format(force))
        verbose = self.wdgtOptions[1][0].value()
        print('Verbosity:\t{}'.format(verbose))
        subpath = self.lneSubpath.text()
        if not subpath:
            subpath = 'DICOM_TEMP'
        for idx in range(self.lstInput.count()):
            part_begin = time.time()
            # extract input filepaths
            in_dirpath = self.lstInput.item(idx).data(0)
            print('Input:\t{}'.format(in_dirpath))
            # extract output filepath
            out_dirpath = self.lneOutput.text()
            print('Output:\t{}'.format(out_dirpath))
            # core actions (import and sort)
            if self.chkActions[0].isChecked():
                dcm_dirpaths = import_sources(
                    in_dirpath, out_dirpath, False, subpath, force, verbose)
            else:
                dcm_dirpaths = [in_dirpath]
            for dcm_dirpath in dcm_dirpaths:
                base_dirpath = os.path.dirname(dcm_dirpath)
                if self.chkActions[1].isChecked():
                    sorting(
                        dcm_dirpath,
                        dcmlib.D_SUMMARY + '.' + dcmlib.JSON_EXT,
                        force, verbose)
                # optional actions
                actions = [(a, x[3])
                    for x, c, a in zip(
                    self.actions[2:], self.chkActions[2:], dcmlib.D_ACTIONS)
                    if c.isChecked()]
                for action, subdir in actions:
                    if action[0] == 'report':
                        os.path.join(base_dirpath, self.actions[5][3])
                    else:
                        i_dirpath = dcm_dirpath
                    o_dirpath = os.path.join(base_dirpath, subdir)
                    if verbose >= VERB_LVL['debug']:
                        print('II:  input dir: {}'.format(i_dirpath))
                        print('II: output dir: {}'.format(o_dirpath))
                    func, params = action
                    func = globals()[func]
                    params = [(vars()[par[2:]]
                        if str(par).startswith('::') else par)
                        for par in params]
                    if verbose >= VERB_LVL['debug']:
                        print('DBG: {}'.format(params))
                    func(*params, force=force, verbose=verbose)
            part_end = time.time()
            if verbose > VERB_LVL['none']:
                print('TotExecTime:\t{}\n'.format(
                    datetime.timedelta(0, part_end - part_begin)))
        tot_end = time.time()
        if verbose > VERB_LVL['none']:
            print('TotExecTime:\t{}'.format(
                datetime.timedelta(0, tot_end - tot_begin)))

    def btnImport_onClicked(self, event=None):
        title = self.btnImport.text().strip('&') + ' ' + \
            self.lblInput.text()[:-1] + ' List'
        target = PySide.QtGui.QFileDialog.getOpenFileName(
            self, title, '.', '*.json')[0]
        if target:
            try:
                with open(target, 'r') as target_file:
                    input_list = json.load(target_file)
                for item in input_list:
                    self.lstInput.addItem(item)
            except:
                title = self.btnImport.text().strip('&') + ' Failed'
                msg = 'Could not import input list from:\n{}'.format(target)
                PySide.QtGui.QMessageBox.warning(
                    self, title, msg, PySide.QtGui.QMessageBox.Ok)

    def btnExport_onClicked(self, event=None):
        title = self.btnExport.text().strip('&') + ' ' + \
            self.lblInput.text()[:-1] + ' List'
        target = PySide.QtGui.QFileDialog.getSaveFileName(
            self, title, '.', '*.json')[0]
        if target:
            input_list = []
            for idx in range(self.lstInput.count()):
                input_list.append(self.lstInput.item(idx).data(0))
            if not input_list:
                title = self.btnExport.text().strip('&')
                msg = self.lblInput.text()[:-1] + ' list is empty. ' + \
                    'Do you want to proceed exporting?'
                proceed = PySide.QtGui.QMessageBox.warning(
                    self, title, msg, PySide.QtGui.QMessageBox.No,
                    PySide.QtGui.QMessageBox.Yes)
            else:
                proceed = True
            if proceed:
                with open(target, 'w') as target_file:
                    json.dump(
                        input_list, target_file, sort_keys=True, indent=4)

    def btnAdd_onClicked(self, event=None):
        # TODO: select multiple directories?
        title = self.btnAdd.text().strip('&') + ' ' + self.lblInput.text()[:-1]
        target = PySide.QtGui.QFileDialog.getExistingDirectory(
            self, title, D_INPUT_DIR)
        if target:
            self.lstInput.addItem(target)
        return target

    def btnRemove_onClicked(self, event=None):
        # TODO: confirmation?
        for item in self.lstInput.selectedItems():
            self.lstInput.takeItem(self.lstInput.row(item))
            # print(item.data(0))  # DEBUG

    def btnClear_onClicked(self, event=None):
        # TODO: confirmation?
        for idx in range(self.lstInput.count()):
            self.lstInput.takeItem(0)

    def lneOutput_onClicked(self, event):
        title = self.lblOutput.text()[:-1]
        target = PySide.QtGui.QFileDialog.getExistingDirectory(
            self, title, D_OUTPUT_DIR)
        if target:
            self.lneOutput.setText(target)
        return target

    def chkImport_stateChanged(self):
        self.lneSubpath.setEnabled(self.chkActions[0].isChecked())
        self.chkActions[1].setEnabled(not self.chkActions[0].isChecked())
        if self.chkActions[0].isChecked():
            self.chkActions[1].setChecked(True)


# ======================================================================
if __name__ == '__main__':
    begin_time = time.time()

    app = PySide.QtGui.QApplication(sys.argv)
    main = Main()
    sys.exit(app.exec_())

    end_time = time.time()
    print('ExecTime: ', datetime.timedelta(0, end_time - begin_time))
