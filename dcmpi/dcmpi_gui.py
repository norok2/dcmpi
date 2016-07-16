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
import argparse  # Parser for command-line options, arguments and subcommands
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
    import tkinter.messagebox as messagebox
    import tkinter.filedialog as filedialog
except ImportError:
    import Tkinter as tk
    import ttk
    import tkMessageBox as messagebox
    import tkFileDialog as filedialog

# Configuration file parser
try:
    import configparser
except ImportError:
    import ConfigParser as configparser

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
from dcmpi.do_import_sources import do_import_sources
from dcmpi.do_sorting import sorting
from dcmpi.dcmpi_cli import dcmpi_cli
from dcmpi.get_nifti import get_nifti
from dcmpi.get_info import get_info
from dcmpi.get_prot import get_prot
from dcmpi.get_meta import get_meta
from dcmpi.get_backup import get_backup
from dcmpi.get_report import get_report
import dcmpi.common as dpc
from dcmpi import INFO
from dcmpi import VERB_LVL, D_VERB_LVL
from dcmpi import msg, dbg

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
        'output_subpath': '{study}/{name}_{date}_{time}_{sys}/dcm',
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
class Main(ttk.Frame):
    def __init__(self, parent, args):
        # get config data
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


        self.actions = [
            ('do_import_sources', 'Import Sources', True, None),
            ('sorting', 'Sort DICOM', True, None),
            ('get_nifti', 'Get NIfTI images', True, dpc.ID['nifti']),
            ('get_meta', 'Get metadata', True, dpc.ID['meta']),
            ('get_prot', 'Get protocol', True, dpc.ID['prot']),
            ('get_info', 'Get information', True, dpc.ID['info']),
            ('get_report', 'Create Report', True, dpc.ID['get_report']),
            ('get_backup', 'Backup DICOM Sources', True, dpc.ID['get_backup']),
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
        self.parent.protocol('WM_DELETE_WINDOW', self.onClose)

        self.style = ttk.Style()
        # print(self.style.theme_names())
        self.style.theme_use('default')
        self.pack(fill=tk.BOTH, expand=True)

        self.frmMain = ttk.Frame(self)
        self.frmMain.pack(fill=tk.BOTH, padx=8, pady=8, expand=True)
        self.lblSpacers = []

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
        self.trvInput.bind('<Double-Button>', self.btnAdd_onClicked)
        self.trvInput.pack(fill=tk.BOTH, padx=1, pady=1, expand=True)
        self.btnImport = ttk.Button(
            self.frmInput, text='Import', compound=tk.LEFT,
            command=self.btnImport_onClicked)
        self.btnImport.pack(side=tk.LEFT, padx=4, pady=4)
        self.btnExport = ttk.Button(
            self.frmInput, text='Export', compound=tk.LEFT,
            command=self.btnExport_onClicked)
        self.btnExport.pack(side=tk.LEFT, padx=4, pady=4)
        spacer = ttk.Label(self.frmInput)
        spacer.pack(side=tk.LEFT, anchor='e', expand=True)
        self.lblSpacers.append(spacer)
        self.btnAdd = ttk.Button(
            self.frmInput, text='Add', compound=tk.LEFT,
            command=self.btnAdd_onClicked)
        self.btnAdd.pack(side=tk.LEFT, anchor='e', padx=4, pady=4)
        self.btnRemove = ttk.Button(
            self.frmInput, text='Remove', compound=tk.LEFT,
            command=self.btnRemove_onClicked)
        self.btnRemove.pack(side=tk.LEFT, anchor='e', padx=4, pady=4)
        self.btnClear = ttk.Button(
            self.frmInput, text='Clear', compound=tk.LEFT,
            command=self.btnClear_onClicked)
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
        self.entPath.bind('<Double-Button>', self.entPath_onClicked)
        self.entPath.pack(
            side=tk.LEFT, fill=tk.X, padx=1, pady=1, expand=True)

        self.frmSubpath = ttk.Frame(self.frmOutput)
        self.frmSubpath.pack(fill=tk.X, expand=True)
        self.lblSubpath = ttk.Label(self.frmSubpath, text='Subpath', width=8)
        self.lblSubpath.pack(side=tk.LEFT, fill=tk.X, padx=1, pady=1)
        self.entSubpath = ttk.Entry(self.frmSubpath)
        self.entSubpath.insert(0, self.cfg['output_subpath'])
        self.entSubpath.pack(
            side=tk.LEFT, fill=tk.X, padx=1, pady=1, expand=True)

        # right frame
        self.frmRight = ttk.Frame(self.frmMain)
        self.frmRight.pack(side=tk.RIGHT, fill=tk.BOTH, padx=4, pady=4)

        self.lblActions = ttk.Label(self.frmRight, text='Actions')
        self.lblActions.pack(padx=1, pady=1)
        self.chkActions = []
        for i, (id_name, name, default, subdir) in enumerate(self.actions):
            checkbox = ttk.Checkbutton(self.frmRight, text=name)
            checkbox.pack(fill=tk.X, padx=1, pady=1)
            if default:
                checkbox.state(['selected'])
            if id_name == 'do_import_sources':
                checkbox.config(command=self.chkActionImport_stateChanged)
            self.chkActions.append(checkbox)
        self.chkActionImport_stateChanged()

        self.lblOptions = ttk.Label(self.frmRight, text='Options')
        self.lblOptions.pack(padx=1, pady=1)
        self.wdgtOptions = []
        for i, (name, val_type, default, extra) in enumerate(self.options):
            if val_type == bool:
                checkbox = ttk.Checkbutton(self.frmRight, text=name)
                checkbox.pack(fill=tk.X, padx=1, pady=1)
                if default:
                    checkbox.state(['selected'])
                self.wdgtOptions.append((checkbox,))
            elif val_type == int:
                frame = ttk.Frame(self.frmRight)
                frame.pack(fill=tk.X, padx=1, pady=1)
                label = ttk.Label(frame, text=name)
                label.pack(side=tk.LEFT, fill=tk.X, padx=1, pady=1)
                spinbox = Spinbox(frame, from_=extra[0], to=extra[1], width=3)
                while not spinbox.get() == str(default):
                    spinbox.invoke('buttonup')
                spinbox.pack(
                    side=tk.LEFT, fill=tk.X, padx=1, pady=1, expand=True)
                self.wdgtOptions.append((frame, label, spinbox))

        self.frmButtons = ttk.Frame(self.frmRight)
        self.frmButtons.pack(side=tk.BOTTOM, padx=4, pady=4)
        spacer = ttk.Label(self.frmButtons)
        spacer.pack(side=tk.LEFT, anchor='e', expand=True)
        self.lblSpacers.append(spacer)
        self.btnRun = ttk.Button(
            self.frmButtons, text='Run', compound=tk.LEFT,
            command=self.btnRun_onClicked)
        self.btnRun.pack(side=tk.LEFT, padx=4, pady=4)
        self.btnClose = ttk.Button(
            self.frmButtons, text='Close', compound=tk.LEFT,
            command=self.onClose)
        self.btnClose.pack(side=tk.LEFT, padx=4, pady=4)

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

    def btnRun_onClicked(self, event=None):
        """Action on Click Button Run"""
        # TODO: redirect stdout to log box
        # TODO: run as a separate process (eventually in parallel?)
        tot_begin = time.time()
        # extract options
        force = 'selected' in self.wdgtOptions[0][0].state()
        msg('Force: {}'.format(force))
        verbose = int(self.wdgtOptions[1][2].get())
        msg('Verb.: {}'.format(verbose))
        subpath = self.entSubpath.get()
        msg('Subpath: {}'.format(subpath))
        if not subpath:
            subpath = 'DICOM_TEMP'
        in_dirpaths = [
            self.trvInput.item(child, 'text')
            for child in self.trvInput.get_children('')]
        for in_dirpath in in_dirpaths:
            part_begin = time.time()
            # extract input filepaths
            msg('Input: {}'.format(in_dirpath), verbose)
            # extract output filepath
            out_dirpath = self.entPath.get()
            msg('Output: {}'.format(out_dirpath), verbose)
            # core actions (import and sort)
            if 'selected' in self.chkActions[0].state():
                print(in_dirpath, out_dirpath, subpath, force, verbose)
                dcm_dirpaths = do_import_sources(
                    in_dirpath, out_dirpath, False, subpath, force, verbose)
            else:
                dcm_dirpaths = [in_dirpath]
            for dcm_dirpath in dcm_dirpaths:
                base_dirpath = os.path.dirname(dcm_dirpath)
                if 'selected' in self.chkActions[1].state():
                    sorting(
                        dcm_dirpath,
                        dpc.D_SUMMARY + '.' + dpc.EXT['json'],
                        force, verbose)
                # optional actions
                actions = [
                    (a, x[3])
                    for x, c, a in zip(self.actions[2:], self.chkActions[2:],
                                       dpc.D_ACTIONS)
                    if 'selecte' in c.state()]
                msg(actions)
                for action, subdir in actions:
                    if action[0] == 'get_report':
                        i_dirpath = os.path.join(
                            base_dirpath, self.actions[5][3])
                    else:
                        i_dirpath = dcm_dirpath
                    o_dirpath = os.path.join(base_dirpath, subdir)
                    if verbose >= VERB_LVL['low']:
                        print('II:  input dir: {}'.format(i_dirpath))
                        print('II: output dir: {}'.format(o_dirpath))
                    func, params = action
                    func = globals()[func]
                    params = [
                        (vars()[par[2:]]
                         if str(par).startswith('::') else par)
                        for par in params]
                    if verbose >= VERB_LVL['low']:
                        print('DBG: {} {}'.format(func, params))
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

    def btnExport_onClicked(self, event=None):
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

    def btnAdd_onClicked(self, event=None):
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

    def btnRemove_onClicked(self, event=None):
        """Action on Click Button Remove"""
        selected = self.trvInput.selection()
        for item in selected:
            self.trvInput.delete(item)

    def btnClear_onClicked(self, event=None):
        """Action on Click Button Clear"""
        items = self.trvInput.get_children('')
        for item in items:
            self.trvInput.delete(item)

    def entPath_onClicked(self, event=None):
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

    def chkActionImport_stateChanged(self, event=None):
        """Action on Change Checkbox Import"""
        is_import = 'selected' in self.chkActions[0].state()
        self.entSubpath['state'] = 'enabled' if is_import else 'disabled'
        self.chkActions[1]['state'] = \
            'enabled' if not is_import else 'disabled'
        if is_import:
            self.chkActions[1].state(['selected'])

    def onClose(self, event=None):
        save_config(self.get_config_from_ui(), self.cfg_filepath)
        if messagebox.askokcancel('Quit', 'Are you sure you want to quit?'):
            self.parent.destroy()


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
    # win = {'w': 760, 'h': 460}
    # screen = {
    #     'w': root.winfo_screenwidth(), 'h': root.winfo_screenheight()}
    # left = screen['w'] // 2 - win['w'] // 2
    # top = screen['h'] // 2 - win['h'] // 2
    # root.geometry(
    #     '{w:d}x{h:d}+{l:d}+{t:d}'.format(l=left, t=top, **win))
    app = Main(root, args)
    root.mainloop()

    end_time = time.time()
    print('ExecTime: ', datetime.timedelta(0, end_time - begin_time))


# ======================================================================
if __name__ == '__main__':
    main()
