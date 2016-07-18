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
import collections  # High-performance container datatypes
import argparse  # Parser for command-line options, arguments and subcommands
# import itertools  # Functions creating iterators for efficient looping
# import functools  # Higher-order functions and operations on callable objects
# import subprocess  # Subprocess management
import multiprocessing  # Process-based parallelism
# import csv  # CSV File Reading and Writing [CSV: Comma-Separated Values]
import json  # JSON encoder and decoder [JSON: JavaScript Object Notation]

# Python interface to Tcl/Tk
try:
    import tkinter as tk
    import tkinter.ttk as ttk
    import tkinter.messagebox as messagebox
    import tkinter.filedialog as filedialog
    import tkinter.simpledialog as simpledialog
except ImportError:
    import Tkinter as tk
    import ttk
    import tkMessageBox as messagebox
    import tkFileDialog as filedialog
    import tkSimpleDialog as simpledialog

# Configuration file parser
# try:
#     import configparser
# except ImportError:
#     import ConfigParser as configparser

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
import appdirs

# :: External Imports Submodules
# import matplotlib.pyplot as plt  # Matplotlib's pyplot: MATLAB-like syntax
# import mayavi.mlab as mlab  # Mayavi's mlab: MATLAB-like syntax
# import scipy.optimize  # SciPy: Optimization Algorithms
# import scipy.integrate  # SciPy: Integrations facilities
# import scipy.constants  # SciPy: Mathematal and Physical Constants
# import scipy.ndimage  # SciPy: ND-image Manipulation

# :: Local Imports
from dcmpi.dcmpi_cli import dcmpi_cli
import dcmpi.common as dpc
from dcmpi import INFO
from dcmpi import VERB_LVL, D_VERB_LVL
from dcmpi import msg, dbg
from dcmpi import MY_GREETINGS

# ======================================================================
DIRS = appdirs.AppDirs(INFO['name'], INFO['author'])
CFG_FILENAME = os.path.splitext(os.path.basename(__file__))[0] + '.json'
CFG_DIRPATHS = (
    os.path.dirname(__file__),
    DIRS.user_config_dir,
    os.getenv('HOME'),
    DIRS.site_config_dir)


# ======================================================================
def default_config():
    """

    Args:
        cfg_filepath ():

    Returns:

    """
    cfg = {
        'input_dir': os.getenv('HOME'),
        'input_dirs': [],
        'output_dir': os.getenv('HOME'),
        'output_subpath': '{study}/{name}_{date}_{time}_{sys}',
        'use_mp': True,
        'num_processes': multiprocessing.cpu_count(),
    }
    return cfg


# ======================================================================
def load_config(
        cfg_filepath=CFG_FILENAME):
    """

    Args:
        cfg_filepath ():

    Returns:

    """
    cfg = {}
    if os.path.exists(cfg_filepath):
        msg('Load configuration from `{}`.'.format(cfg_filepath))
        with open(cfg_filepath, 'r') as cfg_file:
            cfg = json.load(cfg_file)
    return cfg


# ======================================================================
def save_config(
        config,
        cfg_filepath=CFG_FILENAME):
    """

    Args:
        config ():
        cfg_filepath ():

    Returns:

    """
    msg('Save configuration from `{}`.'.format(cfg_filepath))
    dirpath = os.path.dirname(cfg_filepath)
    if not os.path.isdir(dirpath):
        os.makedirs(dirpath)
    with open(cfg_filepath, 'w') as cfg_file:
        json.dump(config, cfg_file, sort_keys=True, indent=4)


# ======================================================================
def centered(target, container=None, width=None, height=None):
    target.update_idletasks()
    if not container:
        container = target.parent
    screen = container.winfo_screenwidth(), \
             container.winfo_screenheight()
    if not width:
        for val in (target.winfo_width(), screen[0] // 3):
            if val > 1:
                width = val
                break
    if not height:
        for val in (target.winfo_height(), screen[1] // 3):
            if val > 1:
                height = val
                break
    left = screen[0] // 2 - width // 2
    top = screen[1] // 2 - height // 2
    container.geometry(
        '{w:d}x{h:d}+{l:d}+{t:d}'.format(
            l=left, t=top, w=width, h=height))


# ======================================================================
class Spinbox(tk.Spinbox):
    def __init__(self, *args, **kwargs):
        tk.Spinbox.__init__(self, *args, **kwargs)
        self.bind('<MouseWheel>', self.mouseWheel)
        self.bind('<Button-4>', self.mouseWheel)
        self.bind('<Button-5>', self.mouseWheel)

    def mouseWheel(self, event):
        if event.num == 5 or event.delta == -120:
            self.invoke('buttondown')
        elif event.num == 4 or event.delta == 120:
            self.invoke('buttonup')


# ======================================================================
class About(tk.Toplevel):
    def __init__(self, parent):
        self.win = tk.Toplevel.__init__(self, parent)
        self.transient(parent)
        self.parent = parent
        self.title('About {}'.format(INFO['name']))
        self.resizable(False, False)
        self.frame = ttk.Frame(self)
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.frmMain = ttk.Frame(self.frame)
        self.frmMain.pack(fill=tk.BOTH, padx=1, pady=1, expand=True)

        about_txt = '\n'.join((
            MY_GREETINGS[1:-1],
            'DCMPI: DICOM Preprocess Interface',
            __doc__,
            '{} - ver. {}\n{} {}\n{}'.format(
                INFO['name'], INFO['version'],
                INFO['copyright'], INFO['author'], INFO['notice'])
        ))
        print(about_txt)
        self.lblInfo = ttk.Label(
            self.frmMain, text=about_txt, anchor=tk.CENTER,
            background='#333', foreground='#ccc', font='TkFixedFont')
        self.lblInfo.pack(padx=8, pady=8, ipadx=8, ipady=8)

        self.btnClose = ttk.Button(
            self.frmMain, text='Close', command=self.destroy)
        self.btnClose.pack(side=tk.BOTTOM, padx=8, pady=8)
        self.bind('<Return>', self.destroy)
        self.bind('<Escape>', self.destroy)

        centered(self.frame, self)

        self.grab_set()
        self.wait_window(self)


# ======================================================================
class Config(tk.Toplevel):
    def __init__(self, parent, app):
        self.settings = collections.OrderedDict((
            ('use_mp', {
                'label': 'Use parallel processing',
                'dtype': bool,
                'default': app.cfg['use_mp'],}),
            ('num_processes', {
                'label': 'Number of parallel processes',
                'dtype': int,
                'default': app.cfg['num_processes'],
                'values': list(range(1, 2 * multiprocessing.cpu_count())),}),
        ))
        self.result = None

        self.win = tk.Toplevel.__init__(self, parent)
        self.transient(parent)
        self.parent = parent
        self.app = app
        self.title('{} Configuration'.format(INFO['name']))
        self.frame = ttk.Frame(self)
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.frmMain = ttk.Frame(self.frame)
        self.frmMain.pack(fill=tk.BOTH, padx=8, pady=8, expand=True)

        self.frmSpacers = []

        self.wdgOptions = {}
        for name, info in self.settings.items():
            if info['dtype'] == bool:
                checkbox = ttk.Checkbutton(self.frmMain, text=info['label'])
                checkbox.pack(fill=tk.X, padx=1, pady=1)
                if info['default']:
                    checkbox.state(['selected'])
                self.wdgOptions[name] = (checkbox,)
            elif info['dtype'] == int:
                frame = ttk.Frame(self.frmMain)
                frame.pack(fill=tk.X, padx=1, pady=1)
                label = ttk.Label(frame, text=info['label'])
                label.pack(side=tk.LEFT, fill=tk.X, padx=1, pady=1)
                spinbox = Spinbox(frame, values=info['values'], width=3)
                while not spinbox.get() == str(info['default']):
                    spinbox.invoke('buttonup')
                spinbox.pack(
                    side=tk.LEFT, fill=tk.X, anchor=tk.W, padx=1, pady=1)
                self.wdgOptions[name] = (frame, label, spinbox)

        self.frmButtons = ttk.Frame(self.frmMain)
        self.frmButtons.pack(side=tk.BOTTOM, padx=4, pady=4)
        spacer = ttk.Frame(self.frmButtons)
        spacer.pack(side=tk.LEFT, anchor='e', expand=True)
        self.frmSpacers.append(spacer)
        self.btnOK = ttk.Button(
            self.frmButtons, text='OK', compound=tk.LEFT,
            command=self.ok)
        self.btnOK.pack(side=tk.LEFT, padx=4, pady=4)
        self.btnReset = ttk.Button(
            self.frmButtons, text='Reset', compound=tk.LEFT,
            command=self.reset)
        self.btnReset.pack(side=tk.LEFT, padx=4, pady=4)
        self.btnCancel = ttk.Button(
            self.frmButtons, text='Cancel', compound=tk.LEFT,
            command=self.cancel)
        self.btnCancel.pack(side=tk.LEFT, padx=4, pady=4)
        self.bind('<Return>', self.ok)
        self.bind('<Escape>', self.cancel)

        centered(self.frame, self)

        self.grab_set()
        self.wait_window(self)

    # --------------------------------
    def ok(self, event=None):
        if not self.validate():
            return
        self.withdraw()
        self.update_idletasks()
        self.apply()
        self.cancel()

    def cancel(self, event=None):
        # put focus back to the parent window
        self.parent.focus_set()
        self.destroy()

    def reset(self, event=None):
        for name, vals in self.settings.items():
            if vals['dtype'] == bool:
                self.wdgOptions[name][0].state(
                    ['selected' if self.app.cfg[name] else 'normal'])
            elif vals['dtype'] == int:
                self.wdgOptions[name][2].delete(0, tk.END)
                self.wdgOptions[name][2].insert(0, str(self.app.cfg[name]))

    def validate(self, event=None):
        return True

    def apply(self, event=None):
        self.result = {}
        for name, vals in self.settings.items():
            if vals['dtype'] == bool:
                self.result[name] = \
                    'selected' in self.wdgOptions[name][0].state()
            elif vals['dtype'] == int:
                self.result[name] = self.wdgOptions[name][2].get()


# ======================================================================
class Main(ttk.Frame):
    def __init__(self, parent, args):
        # get config data
        cfg = {}
        self.cfg = default_config()
        for dirpath in CFG_DIRPATHS:
            self.cfg_filepath = os.path.join(dirpath, args.config)
            cfg = load_config(self.cfg_filepath)
            if cfg:
                break
        if cfg:
            self.cfg.update(cfg)
        else:
            self.cfg_filepath = os.path.join(
                DIRS.user_config_dir, CFG_FILENAME)

        self.modules = collections.OrderedDict([
            ('import_subpath', {
                'label': 'DICOM',
                'default': True,
                'extra_subpath': dpc.ID['dicom']}),
            ('niz_subpath', {
                'label': 'NIfTI Image',
                'default': True,
                'extra_subpath': dpc.ID['nifti']}),
            ('meta_subpath', {
                'label': 'Metadata',
                'default': True,
                'extra_subpath': dpc.ID['meta']}),
            ('prot_subpath', {
                'label': 'Protocol',
                'default': True,
                'extra_subpath': dpc.ID['prot']}),
            ('info_subpath', {
                'label': 'Information',
                'default': True,
                'extra_subpath': dpc.ID['info']}),
            ('report_tpl', {
                'label': 'Report template',
                'default': True,
                'template': dpc.TPL['report']}),
            ('backup_tpl', {
                'label': 'Backup template',
                'default': True,
                'template': dpc.TPL['backup']}),
        ])
        self.options = collections.OrderedDict((
            ('force', {
                'label': 'Force',
                'dtype': bool,
                'default': False}),
            ('verbose', {
                'label': 'Verbosity',
                'dtype': int,
                'default': D_VERB_LVL,
                'values': list(range(VERB_LVL['none'], VERB_LVL['debug']))}),
        ))

        # :: initialization of the UI
        ttk.Frame.__init__(self, parent)
        self.parent = parent
        self.parent.title('DCMPI: DICOM Preprocessing Interface')
        self.parent.protocol('WM_DELETE_WINDOW', self.actionExit)

        self.style = ttk.Style()
        # print(self.style.theme_names())
        self.style.theme_use('clam')
        self.pack(fill=tk.BOTH, expand=True)

        self.mnuMain = tk.Menu(self.parent, tearoff=False)
        self.parent.config(menu=self.mnuMain)
        self.mnuFile = tk.Menu(self.mnuMain, tearoff=False)
        self.mnuMain.add_cascade(label='File', menu=self.mnuFile)
        self.mnuFileInput = tk.Menu(self.mnuFile, tearoff=False)
        self.mnuFile.add_cascade(label='Input', menu=self.mnuFileInput)
        self.mnuFileInput.add_command(label='Add...', command=self.actionAdd)
        self.mnuFileInput.add_command(
            label='Remove', command=self.actionRemove)
        self.mnuFileInput.add_command(
            label='Clear', command=self.actionClear)
        self.mnuFileInput.add_separator()
        self.mnuFileInput.add_command(
            label='Import...', command=self.actionImport)
        self.mnuFileInput.add_command(
            label='Export...', command=self.actionExport)
        self.mnuFileOutput = tk.Menu(self.mnuFile, tearoff=False)
        self.mnuFile.add_cascade(label='Output', menu=self.mnuFileOutput)
        self.mnuFileOutput.add_command(
            label='Path...', command=self.actionPath)
        self.mnuFile.add_separator()
        self.mnuFile.add_command(label='Run', command=self.actionRun)
        self.mnuFile.add_separator()
        self.mnuFile.add_command(label='Config', command=self.actionConfig)
        self.mnuFile.add_separator()
        self.mnuFile.add_command(label='Exit', command=self.actionExit)
        self.mnuHelp = tk.Menu(self.mnuMain, tearoff=False)
        self.mnuMain.add_cascade(label='Help', menu=self.mnuHelp)
        self.mnuHelp.add_command(
            label='Default settings', command=self.resetDefaults)
        self.mnuHelp.add_separator()
        self.mnuHelp.add_command(label='About', command=self.actionAbout)

        self.frmMain = ttk.Frame(self)
        self.frmMain.pack(fill=tk.BOTH, padx=8, pady=8, expand=True)
        self.frmSpacers = []

        # left frame
        self.frmLeft = ttk.Frame(self.frmMain)
        self.frmLeft.pack(
            side=tk.LEFT, fill=tk.BOTH, padx=4, pady=4, expand=True)

        self.frmInput = ttk.Frame(self.frmLeft)
        self.frmInput.pack(
            side=tk.TOP, fill=tk.BOTH, padx=4, pady=4, expand=True)
        self.lblInput = ttk.Label(self.frmInput, text='Input')
        self.lblInput.pack(padx=1, pady=1)
        self.trvInput = ttk.Treeview(self.frmInput, show='tree', height=4)
        self.trvInput.bind('<Double-Button>', self.actionAdd)
        self.trvInput.pack(fill=tk.BOTH, padx=1, pady=1, expand=True)
        self.btnImport = ttk.Button(
            self.frmInput, text='Import', compound=tk.LEFT,
            command=self.actionImport)
        self.btnImport.pack(side=tk.LEFT, padx=4, pady=4)
        self.btnExport = ttk.Button(
            self.frmInput, text='Export', compound=tk.LEFT,
            command=self.actionExport)
        self.btnExport.pack(side=tk.LEFT, padx=4, pady=4)
        spacer = ttk.Frame(self.frmInput)
        spacer.pack(side=tk.LEFT, anchor='e', expand=True)
        self.frmSpacers.append(spacer)
        self.btnAdd = ttk.Button(
            self.frmInput, text='Add', compound=tk.LEFT,
            command=self.actionAdd)
        self.btnAdd.pack(side=tk.LEFT, anchor='e', padx=4, pady=4)
        self.btnRemove = ttk.Button(
            self.frmInput, text='Remove', compound=tk.LEFT,
            command=self.actionRemove)
        self.btnRemove.pack(side=tk.LEFT, anchor='e', padx=4, pady=4)
        self.btnClear = ttk.Button(
            self.frmInput, text='Clear', compound=tk.LEFT,
            command=self.actionClear)
        self.btnClear.pack(side=tk.LEFT, anchor='e', padx=4, pady=4)

        self.frmOutput = ttk.Frame(self.frmLeft)
        self.frmOutput.pack(fill=tk.X, padx=4, pady=4)
        self.lblOutput = ttk.Label(self.frmOutput, text='Output')
        self.lblOutput.pack(side=tk.TOP, padx=1, pady=1)

        self.frmPath = ttk.Frame(self.frmOutput)
        self.frmPath.pack(fill=tk.X, expand=True)
        self.lblPath = ttk.Label(self.frmPath, text='Path', width=8)
        self.lblPath.pack(side=tk.LEFT, fill=tk.X, padx=1, pady=1)
        self.entPath = ttk.Entry(self.frmPath)
        self.entPath.insert(0, self.cfg['output_dir'])
        self.entPath.bind('<Double-Button>', self.actionPath)
        self.entPath.pack(
            side=tk.LEFT, fill=tk.X, padx=1, pady=1, expand=True)

        self.frmSubpath = ttk.Frame(self.frmOutput)
        self.frmSubpath.pack(fill=tk.X, expand=True)
        self.lblSubpath = ttk.Label(self.frmSubpath, text='Sub-Path', width=8)
        self.lblSubpath.pack(side=tk.LEFT, fill=tk.X, padx=1, pady=1)
        self.entSubpath = ttk.Entry(self.frmSubpath)
        self.entSubpath.insert(0, self.cfg['output_subpath'])
        self.entSubpath.pack(
            side=tk.LEFT, fill=tk.X, padx=1, pady=1, expand=True)

        # right frame
        self.frmRight = ttk.Frame(self.frmMain)
        self.frmRight.pack(side=tk.RIGHT, fill=tk.BOTH, padx=4, pady=4)

        self.lblActions = ttk.Label(
            self.frmRight, text='Sub-Paths and Templates')
        self.lblActions.pack(padx=1, pady=1)
        self.wdgModules = {}
        for name, info in self.modules.items():
            frame = ttk.Frame(self.frmRight)
            frame.pack(fill=tk.X, padx=1, pady=1)
            if 'extra_subpath' in info:
                checkbox = ttk.Checkbutton(frame, text=info['label'])
                checkbox.pack(
                    side=tk.LEFT, fill=tk.X, padx=1, pady=1, expand=True)
                if info['default']:
                    checkbox.state(['selected'])
                checkbox.config(command=self.activateModules)
                entry = ttk.Entry(frame, width=8)
                entry.insert(0, info['extra_subpath'])
                entry.pack(side=tk.RIGHT, fill=tk.X, padx=1, pady=1)
            elif 'template' in info:
                checkbox = ttk.Checkbutton(frame, text=info['label'])
                checkbox.pack(fill=tk.X, padx=1, pady=1, expand=True)
                if info['default']:
                    checkbox.state(['selected'])
                checkbox.config(command=self.activateModules)
                entry = ttk.Entry(frame, width=24)
                entry.insert(0, info['template'])
                entry.pack(fill=tk.X, padx=1, pady=1, expand=True)
            else:
                checkbox = ttk.Checkbutton(frame, text=info['label'])
                checkbox.pack(fill=tk.X, padx=1, pady=1, expand=True)
                if info['default']:
                    checkbox.state(['selected'])
                checkbox.config(command=self.activateModules)
                entry = None
            self.wdgModules[name] = (frame, checkbox, entry)

        spacer = ttk.Frame(self.frmRight)
        spacer.pack(side=tk.TOP, padx=4, pady=4)
        self.frmSpacers.append(spacer)
        self.lblOptions = ttk.Label(self.frmRight, text='Options')
        self.lblOptions.pack(padx=1, pady=1)
        self.wdgOptions = {}
        for name, info in self.options.items():
            if info['dtype'] == bool:
                checkbox = ttk.Checkbutton(self.frmRight, text=info['label'])
                checkbox.pack(fill=tk.X, padx=1, pady=1)
                if info['default']:
                    checkbox.state(['selected'])
                self.wdgOptions[name] = (checkbox,)
            elif info['dtype'] == int:
                frame = ttk.Frame(self.frmRight)
                frame.pack(fill=tk.X, padx=1, pady=1)
                label = ttk.Label(frame, text=info['label'])
                label.pack(side=tk.LEFT, fill=tk.X, padx=1, pady=1)
                spinbox = Spinbox(frame, values=info['values'], width=3)
                while not spinbox.get() == str(info['default']):
                    spinbox.invoke('buttonup')
                spinbox.pack(
                    side=tk.LEFT, fill=tk.X, anchor=tk.W, padx=1, pady=1)
                self.wdgOptions[name] = (frame, label, spinbox)

        # spacer = ttk.Frame(self.frmRight)
        # spacer.pack(side=tk.TOP, padx=4, pady=4)
        # self.frmSpacers.append(spacer)
        # self.pbrRunning = ttk.Progressbar(self.frmRight)
        # self.pbrRunning.pack(side=tk.TOP, fill=tk.X, expand=True)

        spacer = ttk.Frame(self.frmRight)
        spacer.pack(side=tk.TOP, padx=4, pady=4)
        self.frmSpacers.append(spacer)
        self.frmButtons = ttk.Frame(self.frmRight)
        self.frmButtons.pack(side=tk.BOTTOM, padx=4, pady=4)
        spacer = ttk.Frame(self.frmButtons)
        spacer.pack(side=tk.LEFT, anchor='e', expand=True)
        self.frmSpacers.append(spacer)
        self.btnRun = ttk.Button(
            self.frmButtons, text='Run', compound=tk.LEFT,
            command=self.actionRun)
        self.btnRun.pack(side=tk.LEFT, padx=4, pady=4)
        self.btnExit = ttk.Button(
            self.frmButtons, text='Exit', compound=tk.LEFT,
            command=self.actionExit)
        self.btnExit.pack(side=tk.LEFT, padx=4, pady=4)

        centered(self)

    # --------------------------------
    def get_config_from_ui(self):
        """Get the config information from the UI"""
        cfg = {
            'input_dirs': [
                self.trvInput.item(child, 'text')
                for child in self.trvInput.get_children('')],
            'output_dir': self.entPath.get(),
            'output_subpath': self.entSubpath.get(),
        }
        return cfg

    def actionRun(self, event=None):
        """Action on Click Button Run"""
        # TODO: redirect stdout to some log box / use progressbar
        tot_begin = time.time()
        # extract options
        force = 'selected' in self.wdgOptions['force'][0].state()
        msg('Force: {}'.format(force))
        verbose = int(self.wdgOptions['verbose'][2].get())
        msg('Verb.: {}'.format(verbose))
        in_dirpaths = [
            self.trvInput.item(child, 'text')
            for child in self.trvInput.get_children('')]
        if self.cfg['use_mp']:
            # parallel
            n_proc = self.cfg['num_processes']
            pool = multiprocessing.Pool(processes=n_proc)
            proc_result_list = []
        for in_dirpath in in_dirpaths:
            dcmpi_cli_kwargs = {
                name: val[2].get()
                for name, val in self.wdgModules.items()}
            dcmpi_cli_kwargs.update({
                'in_dirpath': in_dirpath,
                'out_dirpath': self.entPath.get(),
                'subpath': self.entSubpath.get(),
                'force': force,
                'verbose': verbose,
            })
            print(dcmpi_cli_kwargs)
            if self.cfg['use_mp']:
                proc_result = pool.apply_async(
                    dcmpi_cli, kwds=dcmpi_cli_kwargs)
                proc_result_list.append(proc_result)
            else:
                dcmpi_cli(**dcmpi_cli_kwargs)
        if self.cfg['use_mp']:
            res_list = []
            for proc_result in proc_result_list:
                res_list.append(proc_result.get())
        return

    def actionImport(self, event=None):
        """Action on Click Button Import"""
        title = '{} {} List'.format(
            self.btnImport.cget('text'), self.lblInput.cget('text'))
        in_filepath = filedialog.askopenfilename(
            parent=self, title=title, defaultextension='.json', initialdir='.',
            filetypes=[('JSON Files', '*.json')])
        if in_filepath:
            try:
                with open(in_filepath, 'r') as in_file:
                    targets = json.load(in_file)
                for target in targets:
                    self.trvInput.insert('', tk.END, text=target)
            except ValueError:
                title = self.btnImport.cget('text') + ' Failed'
                msg = 'Could not import input list from `{}`'.format(
                    in_filepath)
                messagebox.showerror(title=title, message=msg)

    def actionExport(self, event=None):
        """Action on Click Button Export"""
        title = '{} {} List'.format(
            self.btnExport.cget('text'), self.lblInput.cget('text'))
        out_filepath = filedialog.asksaveasfilename(
            parent=self, title=title, defaultextension='.json', initialdir='.',
            filetypes=[('JSON Files', '*.json')], confirmoverwrite=True)
        if out_filepath:
            targets = [
                self.trvInput.item(child, 'text')
                for child in self.trvInput.get_children('')]
            if not targets:
                title = self.btnExport.cget('text')
                msg = 'Empty {} list.'.format(self.lblInput.cget('text')) + \
                      'Do you want to proceedporting?'
                proceed = messagebox.askyesno(title=title, message=msg)
            else:
                proceed = True
            if proceed:
                with open(out_filepath, 'w') as out_file:
                    json.dump(targets, out_file, sort_keys=True, indent=4)

    def actionAdd(self, event=None):
        """Action on Click Button Add"""
        title = self.btnAdd.cget('text') + ' ' + self.lblInput.cget('text')
        target = filedialog.askdirectory(
            parent=self, title=title, initialdir=self.cfg['input_dir'],
            mustexist=True)
        targets = [
            self.trvInput.item(child, 'text')
            for child in self.trvInput.get_children('')]
        if target and target not in targets:
            self.trvInput.insert('', tk.END, text=target)
        return target

    def actionRemove(self, event=None):
        """Action on Click Button Remove"""
        items = self.trvInput.get_children('')
        selected = self.trvInput.selection()
        if selected:
            for item in selected:
                self.trvInput.delete(item)
        elif items:
            self.trvInput.delete(items[-1])
        else:
            msg('Empty input list!')

    def actionClear(self, event=None):
        """Action on Click Button Clear"""
        items = self.trvInput.get_children('')
        for item in items:
            self.trvInput.delete(item)

    def actionPath(self, event=None):
        """Action on Click Text Output"""
        title = self.lblOutput.cget('text') + ' ' + self.lblPath.cget('text')
        target = filedialog.askdirectory(
            parent=self, title=title, initialdir=self.cfg['output_dir'],
            mustexist=True)
        if target:
            # self.entPath.config(state='enabled')
            self.entPath.delete(0, tk.END)
            self.entPath.insert(0, target)
            # self.entPath.config(state='readonly')
        return target

    def activateModules(self, event=None):
        """Action on Change Checkbox Import"""
        for items in self.wdgModules:
            active = 'selected' in items[1].state()
            if items[2]:
                items[2]['state'] = 'enabled' if active else 'disabled'

    def actionExit(self, event=None):
        save_config(self.get_config_from_ui(), self.cfg_filepath)
        if messagebox.askokcancel('Quit', 'Are you sure you want to quit?'):
            self.parent.destroy()

    def actionAbout(self, event=None):
        self.winAbout = About(self.parent)

    def actionConfig(self, event=None):
        self.winConfig = Config(self.parent, self)
        if self.winConfig.result:
            self.cfg.update(self.winConfig.result)

    def resetDefaults(self, event=None):
        pass

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
        '-c', '--config', metavar='FILE',
        default=CFG_FILENAME,
        help='specify configuration file name/path [%(default)s]')
    return arg_parser


# ======================================================================
def main():
    # :: handle program parameters
    arg_parser = handle_arg()
    args = arg_parser.parse_args()
    # :: print debug info
    if args.verbose == VERB_LVL['debug']:
        arg_parser.print_help()
        print()
        print('II:', 'Parsed Arguments:', args)
    print(__doc__)
    begin_time = time.time()

    root = tk.Tk()
    app = Main(root, args)
    root.mainloop()

    end_time = time.time()
    print('ExecTime: ', datetime.timedelta(0, end_time - begin_time))


# ======================================================================
if __name__ == '__main__':
    main()
