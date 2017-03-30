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
import time  # Time access and conversions
import datetime  # Basic date and time types
import json  # JSON encoder and decoder [JSON: JavaScript Object Notation]
import warnings  # Warning control

# :: External Imports

# :: External Imports Submodules

# from PySide import QtGui  # PySide: Core module
from PySide import QtGui  # PySide: GUI module

# :: Local Imports
from dcmpi.do_acquire_sources import do_acquire_sources
from dcmpi.do_sorting import sorting
from dcmpi.get_nifti import get_nifti
from dcmpi.get_info import get_info
from dcmpi.get_prot import get_prot
from dcmpi.get_meta import get_meta
from dcmpi.backup import backup
from dcmpi.report import report
import dcmpi.utils as utl
# from dcmpi_cli import INFO, DIRS
from dcmpi import VERB_LVL, D_VERB_LVL, VERB_LVL_NAMES
from dcmpi import msg, dbg

# ======================================================================
D_INPUT_DIR = '/scr/carlos1/xchg/RME/dcm'
D_OUTPUT_DIR = os.path.join(os.getenv('HOME'), 'hd3/data/siemens')
# D_INPUT_DIR = os.path.join(os.getenv('HOME'), 'hd1/TEMP/SOURCE_DICOM')
# D_OUTPUT_DIR = 'os.path.join(os.getenv('HOME'), 'hd1/TEMP/OUTPUT_DICOM')
D_SUBPATH = '{study}/{name}_{date}_{time}_{sys}/dcm'


# ======================================================================
class Main(QtGui.QWidget):
    def __init__(self):
        super(Main, self).__init__()
        self.actions = [
            ('do_acquire_sources', 'Import Sources', True, None),
            ('do_sorting', 'Sort DICOM', True, None),
            ('get_nifti', 'Get NIfTI images', True, utl.ID['niz']),
            ('get_meta', 'Get metadata', True, utl.ID['meta']),
            ('get_prot', 'Get protocol', True, utl.ID['prot']),
            ('get_info', 'Get information', True, utl.ID['info']),
            ('do_report', 'Create Report', True, utl.ID['do_report']),
            ('do_backup', 'Backup DICOM Sources', True, utl.ID['do_backup']),
        ]
        self.options = [
            ('Force', bool, False, None),
            ('Verbosity', int, D_VERB_LVL,
             (VERB_LVL['none'], VERB_LVL['debug'])),
        ]
        self.initUI()

    # --------------------------------
    # :: initialize UI
    def initUI(self):
        """Initialize UI"""
        # :: input
        self.lblInput = QtGui.QLabel('Input:', self)
        self.lstInput = QtGui.QListWidget(self)

        self.btnImport = QtGui.QPushButton('&Import')
        self.btnImport.setIcon(
            self.style().standardIcon(
                QtGui.QStyle.SP_DialogOpenButton))
        self.btnImport.clicked.connect(self.btnImport_onClicked)

        self.btnExport = QtGui.QPushButton('&Export')
        self.btnExport.setIcon(
            self.style().standardIcon(
                QtGui.QStyle.SP_DialogSaveButton))
        self.btnExport.clicked.connect(self.btnExport_onClicked)

        self.btnAdd = QtGui.QPushButton('&Add')
        self.btnAdd.setIcon(
            self.style().standardIcon(
                QtGui.QStyle.SP_DirIcon))
        self.btnAdd.clicked.connect(self.btnAdd_onClicked)

        self.btnRemove = QtGui.QPushButton('&Remove')
        self.btnRemove.setIcon(
            self.style().standardIcon(
                QtGui.QStyle.SP_TrashIcon))
        self.btnRemove.clicked.connect(self.btnRemove_onClicked)

        self.btnClear = QtGui.QPushButton('&Clear')
        self.btnClear.setIcon(
            self.style().standardIcon(
                QtGui.QStyle.SP_DialogResetButton))
        self.btnClear.clicked.connect(self.btnClear_onClicked)

        self.hboxButtonsInput = QtGui.QHBoxLayout()
        self.hboxButtonsInput.addWidget(self.btnImport)
        self.hboxButtonsInput.addWidget(self.btnExport)
        self.hboxButtonsInput.addStretch(1.0)
        self.hboxButtonsInput.addWidget(self.btnAdd)
        self.hboxButtonsInput.addWidget(self.btnRemove)
        self.hboxButtonsInput.addWidget(self.btnClear)

        self.vboxInput = QtGui.QVBoxLayout()
        self.vboxInput.addWidget(self.lblInput)
        self.vboxInput.addWidget(self.lstInput)
        self.vboxInput.addLayout(self.hboxButtonsInput)

        # :: output
        self.lblOutput = QtGui.QLabel('Output:', self)
        self.lblOutput.setMinimumWidth(60)
        out_dirpath = D_OUTPUT_DIR if os.path.isdir(D_OUTPUT_DIR) else '.'
        self.lneOutput = QtGui.QLineEdit(out_dirpath)
        self.lneOutput.setReadOnly(True)
        self.lneOutput.mousePressEvent = self.lneOutput_onClicked

        subpath_help = utl.fill_from_dicom.__doc__
        subpath_help = subpath_help[
                       subpath_help.find('format_str : str\n') +
                       len('format_str : str\n'):
                       subpath_help.find('\n    extra_fields : boolean')]
        subpath_help = subpath_help.replace('        | ', '')
        subpath_help = '\n'.join(subpath_help.split('\n')[1:])
        self.lblSubdir = QtGui.QLabel('Subpath:', self)
        self.lblSubdir.setMinimumWidth(60)
        self.lneSubpath = QtGui.QLineEdit(D_SUBPATH)
        self.lneSubpath.setToolTip(subpath_help)

        self.hboxOutput = QtGui.QHBoxLayout()
        self.hboxOutput.addWidget(self.lblOutput)
        self.hboxOutput.addWidget(self.lneOutput)

        self.hboxSubdir = QtGui.QHBoxLayout()
        self.hboxSubdir.addWidget(self.lblSubdir)
        self.hboxSubdir.addWidget(self.lneSubpath)

        self.vboxOutput = QtGui.QVBoxLayout()
        self.vboxOutput.addLayout(self.hboxOutput)
        self.vboxOutput.addLayout(self.hboxSubdir)

        self.vboxIO = QtGui.QVBoxLayout()
        self.vboxIO.addLayout(self.vboxInput)
        self.vboxIO.addLayout(self.vboxOutput)

        # :: actions
        self.lblActions = QtGui.QLabel('Actions:', self)
        self.chkActions = []
        for name, label, default, subdir in self.actions:
            checkbox = QtGui.QCheckBox(label, self)
            if default:
                checkbox.toggle()
            if name == 'do_acquire_sources':
                checkbox.stateChanged.connect(self.chkImport_stateChanged)
            checkbox.setToolTip('Warning: toggling actions is experimental.')
            self.chkActions.append(checkbox)

        self.vboxActions = QtGui.QVBoxLayout()
        self.vboxActions.addWidget(self.lblActions)
        for checkbox in self.chkActions:
            self.vboxActions.addWidget(checkbox)
        self.vboxActions.addStretch(1.0)

        self.chkImport_stateChanged()

        # :: options
        self.lblOptions = QtGui.QLabel('Options:', self)
        self.wdgtOptions = []
        for name, val_type, default, extra in self.options:
            if val_type == bool:
                widget = QtGui.QCheckBox(name, self)
                if default:
                    widget.checked()
                self.wdgtOptions.append((widget, None, None))
            elif val_type == int:
                label = QtGui.QLabel(name, self)
                widget = QtGui.QSpinBox(self)
                widget.setRange(extra[0], extra[1])
                widget.setValue(default)
                box = QtGui.QHBoxLayout()
                box.addWidget(label)
                box.addWidget(widget)
                self.wdgtOptions.append((widget, label, box))

        self.vboxOptions = QtGui.QVBoxLayout()
        self.vboxOptions.addWidget(self.lblOptions)
        for widget, label, box in self.wdgtOptions:
            if box:
                self.vboxOptions.addLayout(box)
            else:
                self.vboxOptions.addWidget(widget)
        self.vboxOptions.addStretch(1.0)

        self.vboxMore = QtGui.QVBoxLayout()
        self.vboxMore.addLayout(self.vboxActions)
        self.vboxMore.addLayout(self.vboxOptions)

        self.hboxIOAndMore = QtGui.QHBoxLayout()
        self.hboxIOAndMore.addLayout(self.vboxIO)
        self.hboxIOAndMore.addLayout(self.vboxMore)

        # :: buttons
        self.btnRun = QtGui.QPushButton('&Run')
        self.btnRun.setIcon(
            self.style().standardIcon(
                QtGui.QStyle.SP_DialogApplyButton))
        self.btnRun.clicked.connect(self.btnRun_onClicked)

        self.btnClose = QtGui.QPushButton('&Close')
        self.btnClose.setIcon(
            self.style().standardIcon(
                QtGui.QStyle.SP_DialogCloseButton))
        self.btnClose.clicked.connect(self.close)

        self.hboxButtons = QtGui.QHBoxLayout()
        self.hboxButtons.addStretch(1.0)
        self.hboxButtons.addWidget(self.btnRun)
        self.hboxButtons.addWidget(self.btnClose)

        # :: main
        self.vboxMain = QtGui.QVBoxLayout()
        self.vboxMain.addLayout(self.hboxIOAndMore)
        self.vboxMain.addLayout(self.hboxButtons)

        self.setLayout(self.vboxMain)

        self.resize(640, 320)
        self.setWindowTitle('Extract and preprocess DICOM')
        self.setWindowIcon(
            self.style().standardIcon(
                QtGui.QStyle.SP_ComputerIcon))
        self.show()

    # --------------------------------
    # :: actions
    def btnRun_onClicked(self, event=None):
        """Action on Click Button Run"""
        # TODO: redirect stdout to log box
        # TODO: run as a separate process (eventually in parallel?)
        tot_begin = time.time()
        # extract options
        force = self.wdgtOptions[0][0].isChecked()
        print('Force: {}'.format(force))
        verbose = self.wdgtOptions[1][0].value()
        print('Verb.: {}'.format(verbose))
        subpath = self.lneSubpath.text()
        if not subpath:
            subpath = 'DICOM_TEMP'
        for i in range(self.lstInput.count()):
            part_begin = time.time()
            # extract input filepaths
            in_dirpath = self.lstInput.item(i).data(0)
            print('Input:  {}'.format(in_dirpath))
            # extract output filepath
            out_dirpath = self.lneOutput.text()
            print('Output: {}'.format(out_dirpath))
            # core actions (import and sort)
            if self.chkActions[0].isChecked():
                dcm_dirpaths = do_acquire_sources(
                    in_dirpath, out_dirpath, False, subpath, force, verbose)
            else:
                dcm_dirpaths = [in_dirpath]
            for dcm_dirpath in dcm_dirpaths:
                base_dirpath = os.path.dirname(dcm_dirpath)
                if self.chkActions[1].isChecked():
                    sorting(
                        dcm_dirpath,
                        utl.D_SUMMARY + '.' + utl.EXT['json'],
                        force, verbose)
                # optional actions
                actions = [
                    (a, x[3])
                    for x, c, a in zip(
                        self.actions[2:], self.chkActions[2:],
                        utl.D_ACTIONS)
                    if c.isChecked()]
                for action, subdir in actions:
                    if action[0] == 'do_report':
                        i_dirpath = os.path.join(
                            base_dirpath, self.actions[5][3])
                    else:
                        i_dirpath = dcm_dirpath
                    o_dirpath = os.path.join(base_dirpath, subdir)
                    if verbose >= VERB_LVL['debug']:
                        print('I:  input dir: {}'.format(i_dirpath))
                        print('I: output dir: {}'.format(o_dirpath))
                    func, params = action
                    func = globals()[func]
                    params = [
                        (vars()[par[2:]]
                         if str(par).startswith('::') else par)
                        for par in params]
                    if verbose >= VERB_LVL['debug']:
                        print('DBG: {} {}'.format(func, params))
                    func(*params, force=force, verbose=verbose)
            part_end = time.time()
            if verbose > VERB_LVL['none']:
                print('TotExecTime: {}\n'.format(
                    datetime.timedelta(0, part_end - part_begin)))
        tot_end = time.time()
        if verbose > VERB_LVL['none']:
            print('TotExecTime: {}'.format(
                datetime.timedelta(0, tot_end - tot_begin)))

    def btnImport_onClicked(self, event=None):
        """Action on Click Button Import"""
        title = self.btnImport.text().strip('&') + ' ' + \
                self.lblInput.text()[:-1] + ' List'
        target = QtGui.QFileDialog.getOpenFileName(
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
                QtGui.QMessageBox.warning(
                    self, title, msg, QtGui.QMessageBox.Ok)

    def btnExport_onClicked(self, event=None):
        """Action on Click Button Export"""
        title = self.btnExport.text().strip('&') + ' ' + \
                self.lblInput.text()[:-1] + ' List'
        target = QtGui.QFileDialog.getSaveFileName(
            self, title, '.', '*.json')[0]
        if target:
            input_list = []
            for i in range(self.lstInput.count()):
                input_list.append(self.lstInput.item(i).data(0))
            if not input_list:
                title = self.btnExport.text().strip('&')
                msg = self.lblInput.text()[:-1] + ' list is empty. ' + \
                      'Do you want to proceed exporting?'
                proceed = QtGui.QMessageBox.warning(
                    self, title, msg, QtGui.QMessageBox.No,
                    QtGui.QMessageBox.Yes)
            else:
                proceed = True
            if proceed:
                with open(target, 'w') as target_file:
                    json.dump(
                        input_list, target_file, sort_keys=True, indent=4)

    def btnAdd_onClicked(self, event=None):
        """Action on Click Button Add"""
        # TODO: select multiple directories?
        title = self.btnAdd.text().strip('&') + ' ' + self.lblInput.text()[:-1]
        target = QtGui.QFileDialog.getExistingDirectory(
            self, title, D_INPUT_DIR)
        if target:
            self.lstInput.addItem(target)
        return target

    def btnRemove_onClicked(self, event=None):
        """Action on Click Button Remove"""
        # TODO: confirmation?
        for item in self.lstInput.selectedItems():
            self.lstInput.takeItem(self.lstInput.row(item))
            # print(item.data(0))  # DEBUG

    def btnClear_onClicked(self, event=None):
        """Action on Click Button Clear"""
        # TODO: confirmation?
        for i in range(self.lstInput.count()):
            self.lstInput.takeItem(0)

    def lneOutput_onClicked(self, event):
        """Action on Click Text Output"""
        title = self.lblOutput.text()[:-1]
        target = QtGui.QFileDialog.getExistingDirectory(
            self, title, D_OUTPUT_DIR)
        if target:
            self.lneOutput.setText(target)
        return target

    def chkImport_stateChanged(self):
        """Action on Change Checkbox Import"""
        self.lneSubpath.setEnabled(self.chkActions[0].isChecked())
        self.chkActions[1].setEnabled(not self.chkActions[0].isChecked())
        if self.chkActions[0].isChecked():
            self.chkActions[1].setChecked(True)


# ======================================================================
def main():
    """
    Main entry point for the script.
    """
    begin_time = datetime.datetime.now()

    app = QtGui.QApplication(sys.argv)
    main = Main()
    err_code = app.exec_()

    exec_time = datetime.datetime.now() - begin_time
    print('ExecTime: {}'.format(end_time - begin_time))
    sys.exit(err_code)


# ======================================================================
if __name__ == '__main__':
    warnings.warn('This version is deprecated and will be removed soon!')
    main()
