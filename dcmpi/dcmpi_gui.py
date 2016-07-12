#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Extract and preprocess DICOM files.
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

# Python interface to Tcl/Tk
try:
    import tkinter as tk
    import tkinter.ttk as ttk
    import tkinter.messagebox as mbox
except ImportError:
    import Tkinter as tk
    import ttk
    import tkMessageBox as mbox

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

# :: Local Imports
# import mri_tools.modules.base as mrb
# import mri_tools.modules.utils as mru
# import mri_tools.modules.nifti as mrn
# import mri_tools.modules.geometry as mrg
# from mri_tools.modules.sequences import mp2rage
from dcmpi.import_sources import import_sources
from dcmpi.sorting import sorting
from dcmpi.get_nifti import get_nifti
from dcmpi.get_info import get_info
from dcmpi.get_prot import get_prot
from dcmpi.get_meta import get_meta
from dcmpi.backup import backup
from dcmpi.report import report
import dcmpi.common as dcmlib
# from dcmpi import INFO
from dcmpi import VERB_LVL
from dcmpi import D_VERB_LVL
from dcmpi.common import msg

# ======================================================================
D_INPUT_DIR = '/scr/carlos1/xchg/RME/dcm'
D_OUTPUT_DIR = os.path.join(os.getenv('HOME'), 'isar3/data/siemens')
# D_INPUT_DIR = '/scr/isar1/TEMP/SOURCE_DICOM'
# D_OUTPUT_DIR = '/scr/isar1/TEMP/OUTPUT_DICOM'
D_SUBPATH = '{study}/{name}_{date}_{time}_{sys}/dcm'


# ======================================================================
class Main(ttk.Frame):
    def __init__(self, parent):
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

        # :: initialization of the UI
        ttk.Frame.__init__(self, parent)
        self.parent = parent
        self.parent.title('DCMPI: DICOM Preprocessing Interface')

        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.pack(fill=tk.BOTH, expand=True)

        self.frmMain = ttk.Frame(self)
        self.frmMain.pack(fill=tk.BOTH, padx=8, pady=8, expand=True)

        # left frame
        self.frmLeft = ttk.Frame(self.frmMain)
        self.frmLeft.pack(
            side=tk.LEFT, fill=tk.BOTH, padx=4, pady=4, expand=True)

        self.frmInput = ttk.Frame(self.frmLeft)
        self.frmInput.pack(
            side=tk.TOP, fill=tk.BOTH, padx=4, pady=4, expand=True)
        self.lblInput = ttk.Label(self.frmInput, text='Input')
        self.lblInput.pack(side=tk.TOP, padx=1, pady=1)
        self.trvInput = ttk.Treeview(self.frmInput, height=4)
        self.trvInput.pack(fill=tk.BOTH, padx=1, pady=1, expand=True)
        self.btnImport = ttk.Button(
            self.frmInput, text='Import', compound=tk.LEFT,
            command=self.quit)
        self.btnImport.pack(side=tk.LEFT, padx=4, pady=4)
        self.btnExport = ttk.Button(
            self.frmInput, text='Export', compound=tk.LEFT,
            command=self.quit)
        self.btnExport.pack(side=tk.LEFT, padx=4, pady=4)
        self.btnClear = ttk.Button(
            self.frmInput, text='Clear', compound=tk.LEFT,
            command=self.quit)
        self.btnClear.pack(side=tk.RIGHT, padx=4, pady=4)
        self.btnRemove = ttk.Button(
            self.frmInput, text='Remove', compound=tk.LEFT,
            command=self.quit)
        self.btnRemove.pack(side=tk.RIGHT, padx=4, pady=4)
        self.btnAdd = ttk.Button(
            self.frmInput, text='Add', compound=tk.LEFT,
            command=self.quit)
        self.btnAdd.pack(side=tk.RIGHT, padx=4, pady=4)

        self.frmOutput = ttk.Frame(self.frmLeft)
        self.frmOutput.pack(fill=tk.BOTH, padx=4, pady=4, expand=True)
        self.lblOutput = ttk.Label(self.frmOutput, text='Output')
        self.lblOutput.pack(side=tk.TOP, padx=1, pady=1)

        self.frmPath = ttk.Frame(self.frmOutput)
        self.frmPath.pack(fill=tk.BOTH, expand=True)
        self.lblPath = ttk.Label(self.frmPath, text='Path', width=8)
        self.lblPath.pack(side=tk.LEFT, fill=tk.X, padx=1, pady=1)
        self.entPath = ttk.Entry(self.frmPath)
        self.entPath.pack(
            side=tk.LEFT, fill=tk.X, padx=1, pady=1, expand=True)

        self.frmSubpath = ttk.Frame(self.frmOutput)
        self.frmSubpath.pack(fill=tk.BOTH, expand=True)
        self.lblSubpath = ttk.Label(self.frmSubpath, text='Subpath', width=8)
        self.lblSubpath.pack(side=tk.LEFT, fill=tk.X, padx=1, pady=1)
        self.entSubpath = ttk.Entry(self.frmSubpath)
        self.entSubpath.pack(
            side=tk.LEFT, fill=tk.X, padx=1, pady=1, expand=True)

        # right frame
        self.frmRight = ttk.Frame(self.frmMain)
        self.frmRight.pack(side=tk.RIGHT, fill=tk.BOTH, padx=4, pady=4)

        self.lblActions = ttk.Label(self.frmRight, text='Actions')
        self.lblActions.grid(row=0, columnspan=2, padx=1, pady=1)
        self.chkActions = []
        for i, (name, name, default, subdir) in enumerate(self.actions):
            checkbox_var = tk.BooleanVar()
            checkbox = ttk.Checkbutton(
                self.frmRight, text=name, variable=checkbox_var)
            checkbox.grid(row=i + 1, columnspan=2, padx=1, pady=1, sticky='w')
            if default:
                checkbox_var.set(True)
            if name == 'import_sources':
                checkbox.bind('<Button>', self.quit)
            self.chkActions.append((checkbox, checkbox_var))

        self.lblOptions = ttk.Label(self.frmRight, text='Options')
        self.lblOptions.grid(
            row=1 + len(self.chkActions), columnspan=2, padx=1, pady=1)
        self.wdgtOptions = []
        for i, (name, val_type, default, extra) in enumerate(self.options):
            if val_type == bool:
                checkbox_var = tk.BooleanVar()
                checkbox = ttk.Checkbutton(
                    self.frmRight, text=name, variable=checkbox_var)
                checkbox.grid(
                    row=2 + len(self.chkActions) + i, columnspan=2, padx=1,
                    pady=1, sticky='w')
                if default:
                    checkbox_var.set(True)
                self.wdgtOptions.append((checkbox, checkbox_var))
            elif val_type == int:
                label = ttk.Label(self.frmRight, text=name)
                label.grid(
                    row=2 + len(self.chkActions) + i, column=0, padx=1, pady=1,
                    sticky='w')
                spinbox_var = tk.IntVar()
                spinbox = tk.Spinbox(
                    self.frmRight, from_=extra[0], to=extra[1], width=3,
                    textvariable=spinbox_var)
                spinbox_var.set(default)
                spinbox.grid(
                    row=2 + len(self.chkActions) + i, column=1, padx=1, pady=1,
                    sticky='ew')
                self.wdgtOptions.append((spinbox, spinbox_var))

        self.frmButtons = ttk.Frame(self.frmRight)
        self.frmButtons.grid(
            row=2 + len(self.chkActions) + len(self.wdgtOptions),
            columnspan=2, )
        self.btnClose = ttk.Button(
            self.frmButtons, text='Close', compound=tk.LEFT,
            command=self.quit)
        self.btnClose.pack(side=tk.RIGHT, padx=4, pady=4)
        self.btnRun = ttk.Button(
            self.frmButtons, text='Run', compound=tk.LEFT,
            command=self.btnRun_onClicked)
        self.btnRun.pack(side=tk.RIGHT, padx=4, pady=4)

    def btnRun_onClicked(self, event=None):
        """Action on Click Button Run"""
        # TODO: redirect stdout to log box
        # TODO: run as a separate process (eventually in parallel?)
        tot_begin = time.time()
        # # extract options
        # force = self.wdgtOptions[0][0].isChecked()
        # msg('Force:\t{}'.format(force))
        # verbose = self.wdgtOptions[1][0].value()
        # print('Verbosity:\t{}'.format(verbose))
        # subpath = self.lneSubpath.text()
        # if not subpath:
        #     subpath = 'DICOM_TEMP'
        # for i in range(self.lstInput.count()):
        #     part_begin = time.time()
        #     # extract input filepaths
        #     in_dirpath = self.lstInput.item(i).data(0)
        #     print('Input:\t{}'.format(in_dirpath))
        #     # extract output filepath
        #     out_dirpath = self.lneOutput.text()
        #     print('Output:\t{}'.format(out_dirpath))
        #     # core actions (import and sort)
        #     if self.chkActions[0].isChecked():
        #         dcm_dirpaths = import_sources(
        #             in_dirpath, out_dirpath, False, subpath, force, verbose)
        #     else:
        #         dcm_dirpaths = [in_dirpath]
        #     for dcm_dirpath in dcm_dirpaths:
        #         base_dirpath = os.path.dirname(dcm_dirpath)
        #         if self.chkActions[1].isChecked():
        #             sorting(
        #                 dcm_dirpath,
        #                 dcmlib.D_SUMMARY + '.' + dcmlib.JSON_EXT,
        #                 force, verbose)
        #         # optional actions
        #         actions = [
        #             (a, x[3])
        #             for x, c, a in zip(
        #                 self.actions[2:], self.chkActions[2:],
        #                 dcmlib.D_ACTIONS)
        #             if c.isChecked()]
        #         for action, subdir in actions:
        #             if action[0] == 'report':
        #                 i_dirpath = os.path.join(
        #                     base_dirpath, self.actions[5][3])
        #             else:
        #                 i_dirpath = dcm_dirpath
        #             o_dirpath = os.path.join(base_dirpath, subdir)
        #             if verbose >= VERB_LVL['debug']:
        #                 print('II:  input dir: {}'.format(i_dirpath))
        #                 print('II: output dir: {}'.format(o_dirpath))
        #             func, params = action
        #             func = globals()[func]
        #             params = [
        #                 (vars()[par[2:]]
        #                  if str(par).startswith('::') else par)
        #                 for par in params]
        #             if verbose >= VERB_LVL['debug']:
        #                 print('DBG: {} {}'.format(func, params))
        #             func(*params, force=force, verbose=verbose)
        #     part_end = time.time()
        #     if verbose > VERB_LVL['none']:
        #         print('TotExecTime:\t{}\n'.format(
        #             datetime.timedelta(0, part_end - part_begin)))
        # tot_end = time.time()
        # if verbose > VERB_LVL['none']:
        #     print('TotExecTime:\t{}'.format(
        #         datetime.timedelta(0, tot_end - tot_begin)))


# ======================================================================
def main():
    print(__doc__)
    begin_time = time.time()

    root = tk.Tk()
    win = {'w': 760, 'h': 320}
    screen = {
        'w': root.winfo_screenwidth(), 'h': root.winfo_screenheight()}
    left = screen['w'] // 2 - win['w'] // 2
    top = screen['h'] // 2 - win['h'] // 2
    root.geometry(
        '{w:d}x{h:d}+{l:d}+{t:d}'.format(l=left, t=top, **win))
    app = Main(root)
    root.mainloop()

    end_time = time.time()
    print('ExecTime: ', datetime.timedelta(0, end_time - begin_time))


# ======================================================================
if __name__ == '__main__':
    main()
