#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DCMPI: DICOM preprocessing.
"""

# ======================================================================
# :: Future Imports
from __future__ import (
    division, absolute_import, print_function, unicode_literals, )

# ======================================================================
# :: Python Standard Library Imports
import os  # Miscellaneous operating system interfaces
import sys  # System-specific parameters and functions
import platform  # Access to underlying platform’s identifying data
import datetime  # Basic date and time types
import collections  # High-performance container datatypes
import argparse  # Parser for command-line options, arguments and subcommands
import multiprocessing  # Process-based parallelism
import json  # JSON encoder and decoder [JSON: JavaScript Object Notation]
import warnings  # Warning control

# :: External Imports

# :: External Imports Submodules

# from pytk import tk
# from pytk import ttk
from pytk import messagebox
from pytk import filedialog
from pytk import simpledialog

import pytk.utils
import pytk.widgets

# :: Local Imports
import dcmpi
import dcmpi.utils as utl
from dcmpi import DIRS, INFO
from dcmpi import VERB_LVL, D_VERB_LVL, VERB_LVL_NAMES
from dcmpi import msg, dbg
from dcmpi import MY_GREETINGS

from dcmpi import (
    get_nifti, get_meta, get_prot, get_info, do_report, do_backup, )

# ======================================================================
# :: determine initial configuration
try:
    import appdirs

    _app_dirs = appdirs.AppDirs(INFO['name'].lower(), INFO['author'])
    PATHS = {
        'usr_cfg': _app_dirs.user_config_dir,
        'sys_cfg': _app_dirs.site_config_dir,
    }
except ImportError:
    PATHS = {
        'usr_cfg': os.path.realpath('.'),
        'sys_cfg': os.path.dirname(__file__),
    }

CFG_FILENAME = os.path.splitext(os.path.basename(__file__))[0] + '.cfg.json'
CFG_DIRPATHS = (
    PATHS['usr_cfg'],
    os.path.realpath('.'),
    os.getenv('HOME'),
    os.path.dirname(__file__),
    PATHS['sys_cfg'])

ACTIONS = collections.OrderedDict((
    ('niz', (get_nifti.get_nifti,
             dict(in_dirpath='{dcm_dirpath}', out_dirpath='{dirpath[niz]}'))),
    ('meta', (get_meta.get_meta,
              dict(in_dirpath='{dcm_dirpath}', out_dirpath='{dirpath[meta]}'))),
    ('prot', (get_prot.get_prot,
              dict(in_dirpath='{dcm_dirpath}', out_dirpath='{dirpath[prot]}'))),
    ('info', (get_info.get_info,
              dict(in_dirpath='{dcm_dirpath}', out_dirpath='{dirpath[info]}'))),
    ('report', (do_report.do_report,
                dict(in_dirpath='{dcm_dirpath}', out_dirpath='{base_dirpath}',
                    basename='{report_template}'))),
    ('backup', (do_backup.do_backup,
                dict(in_dirpath='{dcm_dirpath}', out_dirpath='{base_dirpath}',
                    basename='{backup_template}'))),))


# ======================================================================
def default_config():
    """

    Args:
        cfg_filepath ():

    Returns:

    """
    cfg = {
        'add_path': os.path.realpath('.'),
        'import_path': os.path.realpath('.'),
        'export_path': os.path.realpath('.'),
        'input_paths': [],
        'output_path': os.path.realpath('.'),
        'output_subpath': '{study}/{name}_{date}_{time}_{sys}',
        'dcm_subpath': utl.ID['dicom'],
        'niz_subpath': utl.ID['niz'],
        'meta_subpath': utl.ID['meta'],
        'prot_subpath': utl.ID['prot'],
        'info_subpath': utl.ID['info'],
        'report_template': utl.TPL['report'],
        'backup_template': utl.TPL['backup'],
        'force': False,
        'verbose': VERB_LVL_NAMES[D_VERB_LVL],
        'use_mp': True,
        'num_processes': multiprocessing.cpu_count(),
        'gui_style_tk': 'default',
        'save_on_exit': True,
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
        try:
            with open(cfg_filepath, 'r') as cfg_file:
                cfg = json.load(cfg_file)
        except json.JSONDecodeError:
            pass
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
def dcmpi_run(
        in_dirpath,
        out_dirpath,
        subpath=utl.TPL['acquire'],
        dcm_subpath=utl.ID['dicom'],
        niz_subpath=utl.ID['niz'],
        meta_subpath=utl.ID['meta'],
        prot_subpath=utl.ID['prot'],
        info_subpath=utl.ID['info'],
        report_template=utl.TPL['report'],
        backup_template=utl.TPL['backup'],
        actions=ACTIONS,
        force=False,
        verbose=D_VERB_LVL):
    """
    Standard preprocessing of DICOM files.

    Args:
        in_dirpath (str): Path to input directory.
        out_dirpath (str): Path to output directory.
        subpath (str):
        dcm_subpath (str):
        niz_subpath (str):
        meta_subpath (str):
        prot_subpath (str):
        info_subpath (str):
        report_template (str):
        backup_template (str):
        actions (dict):
        force (bool): Force new processing.
        verbose (int): Set level of verbosity.

    Returns:
        None.
    """
    from dcmpi.do_acquire_sources import do_acquire_sources
    from dcmpi.do_sorting import sorting

    # import
    dcm_dirpaths = do_acquire_sources(
        in_dirpath, out_dirpath, 'copy', subpath, dcm_subpath, force, verbose)
    for dcm_dirpath in dcm_dirpaths:
        base_dirpath = os.path.dirname(dcm_dirpath)
        # sort
        sorting(
            dcm_dirpath, utl.D_SUMMARY + '.' + utl.EXT['json'],
            force, verbose)
        # run other actions
        dirpath = {
            'niz': niz_subpath,
            'meta': meta_subpath,
            'prot': prot_subpath,
            'info': info_subpath, }
        dirpath = {
            k: os.path.join(base_dirpath, v) for k, v in dirpath.items() if v}
        for action, (func, func_kws) in actions.items():
            kws = func_kws.copy()
            for key, val in kws.items():
                if isinstance(val, str):
                    kws[key] = val.format_map(locals())
            kws.update(dict(force=force, verbose=verbose))
            try:
                func(**kws)
            except Exception as e:
                warnings.warn(str(e))

        msg('Done: {}'.format(dcm_dirpath))


# ======================================================================
class About(pytk.Window):
    def __init__(self, parent):
        self.win = pytk.Window.__init__(self, parent)
        self.transient(parent)
        self.parent = parent
        self.title('About {}'.format(INFO['name']))
        self.resizable(False, False)
        self.frm = pytk.widgets.Frame(self)
        self.frm.pack(fill='both', expand=True)
        self.frmMain = pytk.widgets.Frame(self.frm)
        self.frmMain.pack(fill='both', padx=1, pady=1, expand=True)

        about_txt = '\n'.join((
            MY_GREETINGS[1:],
            dcmpi.__doc__,
            '{} - ver. {}\n{} {}\n{}'.format(
                INFO['name'], INFO['version'],
                INFO['copyright'], INFO['author'], INFO['notice'])
        ))
        msg(about_txt)
        self.lblInfo = pytk.widgets.Label(
            self.frmMain, text=about_txt, anchor='center',
            background='#333', foreground='#ccc', font='TkFixedFont')
        self.lblInfo.pack(padx=8, pady=8, ipadx=8, ipady=8)

        self.btnClose = pytk.widgets.Button(
            self.frmMain, text='Close', command=self.destroy)
        self.btnClose.pack(side='bottom', padx=8, pady=8)
        self.bind('<Return>', self.destroy)
        self.bind('<Escape>', self.destroy)

        pytk.utils.center(self, self.parent)

        self.grab_set()
        self.wait_window(self)


# ======================================================================
class Settings(pytk.Window):
    def __init__(self, parent, app):
        self.settings = collections.OrderedDict((
            ('use_mp', {'label': 'Use parallel processing', 'dtype': bool, }),
            ('num_processes', {
                'label': 'Number of parallel processes',
                'dtype': int,
                'values': {'start': 1, 'stop': 2 * multiprocessing.cpu_count()},
            }),
            ('gui_style_tk', {
                'label': 'GUI Style (Tk)',
                'dtype': tuple,
                'values': app.style.theme_names()
            }),
        ))
        for name, info in self.settings.items():
            self.settings[name]['default'] = app.cfg[name]
        self.result = None

        self.win = pytk.Window.__init__(self, parent)
        self.transient(parent)
        self.parent = parent
        self.app = app
        self.title('{} Advanced Settings'.format(INFO['name']))
        self.frm = pytk.widgets.Frame(self)
        self.frm.pack(fill='both', expand=True)
        self.frmMain = pytk.widgets.Frame(self.frm)
        self.frmMain.pack(fill='both', padx=8, pady=8, expand=True)

        self.frmSpacers = []

        self.wdgOptions = {}
        for name, info in self.settings.items():
            if info['dtype'] == bool:
                chk = pytk.widgets.Checkbox(self.frmMain, text=info['label'])
                chk.pack(fill='x', padx=1, pady=1)
                chk.set_val(info['default'])
                self.wdgOptions[name] = {'chk': chk}
            elif info['dtype'] == int:
                frm = pytk.widgets.Frame(self.frmMain)
                frm.pack(fill='x', padx=1, pady=1)
                lbl = pytk.widgets.Label(frm, text=info['label'])
                lbl.pack(side='left', fill='x', padx=1, pady=1, expand=True)
                spb = pytk.widgets.Spinbox(frm, **info['values'])
                spb.set_val(info['default'])
                spb.pack(
                    side='left', fill='x', anchor='w', padx=1, pady=1)
                self.wdgOptions[name] = {'frm': frm, 'lbl': lbl, 'spb': spb}
            elif info['dtype'] == tuple:
                frm = pytk.widgets.Frame(self.frmMain)
                frm.pack(fill='x', padx=1, pady=1)
                lbl = pytk.widgets.Label(frm, text=info['label'])
                lbl.pack(side='left', fill='x', padx=1, pady=1, expand=True)
                lst = pytk.widgets.Listbox(frm, values=info['values'])
                lst.set_val(info['default'])
                lst.pack(
                    side='left', fill='x', anchor='w', padx=1, pady=1)
                self.wdgOptions[name] = {'frm': frm, 'lbl': lbl, 'lst': lst}

        self.frmButtons = pytk.widgets.Frame(self.frmMain)
        self.frmButtons.pack(side='bottom', padx=4, pady=4)
        spacer = pytk.widgets.Frame(self.frmButtons)
        spacer.pack(side='left', anchor='e', expand=True)
        self.frmSpacers.append(spacer)
        self.btnOK = pytk.widgets.Button(
            self.frmButtons, text='OK', compound='left',
            command=self.ok)
        self.btnOK.pack(side='left', padx=4, pady=4)
        self.btnReset = pytk.widgets.Button(
            self.frmButtons, text='Reset', compound='left',
            command=self.reset)
        self.btnReset.pack(side='left', padx=4, pady=4)
        self.btnCancel = pytk.widgets.Button(
            self.frmButtons, text='Cancel', compound='left',
            command=self.cancel)
        self.btnCancel.pack(side='left', padx=4, pady=4)
        self.bind('<Return>', self.ok)
        self.bind('<Escape>', self.cancel)

        pytk.utils.center(self, self.parent)

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
        for name, info in self.settings.items():
            if info['dtype'] == bool:
                self.wdgOptions[name]['chk'].set_val(self.app.cfg[name])
            elif info['dtype'] == int:
                self.wdgOptions[name]['spb'].set_val(self.app.cfg[name])
            elif info['dtype'] == str:
                self.wdgOptions[name]['ent'].set_val(self.app.cfg[name])
            elif info['dtype'] == tuple:
                self.wdgOptions[name]['lst'].set_val(self.app.cfg[name])

    def validate(self, event=None):
        return True

    def apply(self, event=None):
        self.result = {}
        for name, info in self.settings.items():
            if info['dtype'] == bool:
                self.result[name] = self.wdgOptions[name]['chk'].get_val()
            elif info['dtype'] == int:
                self.result[name] = self.wdgOptions[name]['spb'].get_val()
            elif info['dtype'] == str:
                self.result[name] = self.wdgOptions[name]['ent'].get_val()
            elif info['dtype'] == tuple:
                self.result[name] = self.wdgOptions[name]['lst'].get_val()


# ======================================================================
class Main(pytk.widgets.Frame):
    def __init__(self, parent, args):
        # get_val config data
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
                PATHS['usr_cfg'], CFG_FILENAME)

        self.modules = collections.OrderedDict([
            ('dcm_subpath', {'label': 'DICOM (required)'}),
            ('niz_subpath', {'label': 'NIfTI Image'}),
            ('meta_subpath', {'label': 'Metadata'}),
            ('prot_subpath', {'label': 'Protocol'}),
            ('info_subpath', {'label': 'Information'}),
            ('report_template', {'label': 'Report template'}),
            ('backup_template', {'label': 'Backup template'}),
        ])
        self.options = collections.OrderedDict((
            ('force', {
                'label': 'Force',
                'dtype': bool
            }),
            ('verbose', {
                'label': 'Verbosity',
                'dtype': int,
                'values': {'values': VERB_LVL_NAMES},
            }),
        ))

        # :: initialization of the UI
        pytk.widgets.Frame.__init__(self, parent)
        self.parent = parent
        self.parent.title('DCMPI: DICOM Preprocessing Interface')
        self.parent.protocol('WM_DELETE_WINDOW', self.actionExit)

        self.style = pytk.Style()
        # print(self.style.theme_names())
        self.style.theme_use(self.cfg['gui_style_tk'])
        self.pack(fill='both', expand=True)

        self._make_menu()

        # :: define UI items
        self.frmMain = pytk.widgets.Frame(self)
        self.frmMain.pack(fill='both', padx=8, pady=8, expand=True)
        self.frmSpacers = []

        # left frame
        self.frmLeft = pytk.widgets.Frame(self.frmMain)
        self.frmLeft.pack(
            side='left', fill='both', padx=4, pady=4, expand=True)

        self.frmInput = pytk.widgets.Frame(self.frmLeft)
        self.frmInput.pack(
            side='top', fill='both', padx=4, pady=4, expand=True)
        self.lblInput = pytk.widgets.Label(self.frmInput, text='Input')
        self.lblInput.pack(padx=1, pady=1)
        self.lsvInput = pytk.widgets.Listview(
            self.frmInput, show='tree', height=4)
        self.lsvInput.bind('<Double-Button-1>', self.actionAdd)
        self.lsvInput.pack(fill='both', padx=1, pady=1, expand=True)
        self.btnImport = pytk.widgets.Button(
            self.frmInput, text='Import', compound='left',
            command=self.actionImport)
        self.btnImport.pack(side='left', padx=4, pady=4)
        self.btnExport = pytk.widgets.Button(
            self.frmInput, text='Export', compound='left',
            command=self.actionExport)
        self.btnExport.pack(side='left', padx=4, pady=4)
        spacer = pytk.widgets.Frame(self.frmInput)
        spacer.pack(side='left', anchor='e', expand=True)
        self.frmSpacers.append(spacer)
        self.btnAdd = pytk.widgets.Button(
            self.frmInput, text='Add', compound='left',
            command=self.actionAdd)
        self.btnAdd.pack(side='left', anchor='e', padx=4, pady=4)
        self.btnRemove = pytk.widgets.Button(
            self.frmInput, text='Remove', compound='left',
            command=self.actionRemove)
        self.btnRemove.pack(side='left', anchor='e', padx=4, pady=4)
        self.btnClear = pytk.widgets.Button(
            self.frmInput, text='Clear', compound='left',
            command=self.actionClear)
        self.btnClear.pack(side='left', anchor='e', padx=4, pady=4)

        self.frmOutput = pytk.widgets.Frame(self.frmLeft)
        self.frmOutput.pack(fill='x', padx=4, pady=4)
        self.lblOutput = pytk.widgets.Label(self.frmOutput, text='Output')
        self.lblOutput.pack(side='top', padx=1, pady=1)

        self.frmPath = pytk.widgets.Frame(self.frmOutput)
        self.frmPath.pack(fill='x', expand=True)
        self.lblPath = pytk.widgets.Label(self.frmPath, text='Path', width=8)
        self.lblPath.pack(side='left', fill='x', padx=1, pady=1)
        self.txtPath = pytk.widgets.Text(self.frmPath)
        self.txtPath.insert(0, self.cfg['output_path'])
        self.txtPath.bind('<Double-Button>', self.actionPath)
        self.txtPath.pack(
            side='left', fill='x', padx=1, pady=1, expand=True)

        self.frmSubpath = pytk.widgets.Frame(self.frmOutput)
        self.frmSubpath.pack(fill='x', expand=True)
        self.lblSubpath = pytk.widgets.Label(self.frmSubpath, text='Sub-Path',
            width=8)
        self.lblSubpath.pack(side='left', fill='x', padx=1, pady=1)
        self.txtSubpath = pytk.widgets.Text(self.frmSubpath)
        self.txtSubpath.insert(0, self.cfg['output_subpath'])
        self.txtSubpath.pack(
            side='left', fill='x', padx=1, pady=1, expand=True)

        # right frame
        self.frmRight = pytk.widgets.Frame(self.frmMain)
        self.frmRight.pack(side='right', fill='both', padx=4, pady=4)

        self.lblActions = pytk.widgets.Label(
            self.frmRight, text='Sub-Paths and Templates')
        self.lblActions.pack(padx=1, pady=1)
        self.wdgModules = collections.OrderedDict()
        for name, info in self.modules.items():
            frm = pytk.widgets.Frame(self.frmRight)
            frm.pack(fill='x', padx=1, pady=1)
            if 'subpath' in name:
                chk = pytk.widgets.Checkbox(frm, text=info['label'])
                chk.pack(
                    side='left', fill='x', padx=1, pady=1, expand=True)
                chk.config(command=self.activateModules)
                entry = pytk.widgets.Text(frm, width=8)
                entry.pack(side='right', fill='x', padx=1, pady=1)
            elif 'template' in name:
                chk = pytk.widgets.Checkbox(frm, text=info['label'])
                chk.pack(fill='x', padx=1, pady=1, expand=True)
                # chk.set_val(info['default'])
                chk.config(command=self.activateModules)
                entry = pytk.widgets.Text(frm, width=24)
                entry.pack(fill='x', padx=1, pady=1, expand=True)
            else:
                chk = pytk.widgets.Checkbox(frm, text=info['label'])
                chk.pack(fill='x', padx=1, pady=1, expand=True)
                chk.config(command=self.activateModules)
                entry = None
            self.wdgModules[name] = {
                'frm': frm, 'chk': chk, 'ent': entry}
        # self.wdgModules['dcm_subpath']['chk']['state'] = 'readonly'
        self.activateModules()

        spacer = pytk.widgets.Frame(self.frmRight)
        spacer.pack(side='top', padx=4, pady=4)
        self.frmSpacers.append(spacer)
        self.lblOptions = pytk.widgets.Label(self.frmRight, text='Options')
        self.lblOptions.pack(padx=1, pady=1)
        self.wdgOptions = {}
        for name, info in self.options.items():
            if info['dtype'] == bool:
                chk = pytk.widgets.Checkbox(self.frmRight, text=info['label'])
                chk.pack(fill='x', padx=1, pady=1)
                self.wdgOptions[name] = {'chk': chk}
            elif info['dtype'] == int:
                frm = pytk.widgets.Frame(self.frmRight)
                frm.pack(fill='x', padx=1, pady=1)
                lbl = pytk.widgets.Label(frm, text=info['label'])
                lbl.pack(side='left', fill='x', padx=1, pady=1)
                spb = pytk.widgets.Spinbox(frm, **info['values'])
                spb.pack(
                    side='left', fill='x', anchor='w', padx=1, pady=1)
                self.wdgOptions[name] = {'frm': frm, 'lbl': lbl, 'spb': spb}
            elif info['dtype'] == str:
                pass

        spacer = pytk.widgets.Frame(self.frmRight)
        spacer.pack(side='top', padx=4, pady=4)
        self.frmSpacers.append(spacer)
        self.pbrRunning = pytk.widgets.Progressbar(self.frmRight)
        self.pbrRunning.pack(side='top', fill='x', expand=True)

        spacer = pytk.widgets.Frame(self.frmRight)
        spacer.pack(side='top', padx=4, pady=4)
        self.frmSpacers.append(spacer)
        self.frmButtons = pytk.widgets.Frame(self.frmRight)
        self.frmButtons.pack(side='bottom', padx=4, pady=4)
        spacer = pytk.widgets.Frame(self.frmButtons)
        spacer.pack(side='left', anchor='e', expand=True)
        self.frmSpacers.append(spacer)
        self.btnRun = pytk.widgets.Button(
            self.frmButtons, text='Run', compound='left',
            command=self.actionRun)
        self.btnRun.pack(side='left', padx=4, pady=4)
        self.btnExit = pytk.widgets.Button(
            self.frmButtons, text='Exit', compound='left',
            command=self.actionExit)
        self.btnExit.pack(side='left', padx=4, pady=4)

        pytk.utils.center(self.parent)

        self._cfg_to_ui()

    # --------------------------------
    def _ui_to_cfg(self):
        """Update the config information from the UI."""
        cfg = self.cfg
        cfg.update({
            'input_paths': self.lsvInput.get_items(),
            'output_path': self.txtPath.get(),
            'output_subpath': self.txtSubpath.get(),
            'save_on_exit': bool(self.save_on_exit.get()),
            'gui_style_tk': self.style.theme_use()
        })
        for name, items in self.wdgModules.items():
            cfg[name] = items['ent'].get_val() if items['chk'].get_val() else ''
        for name, items in self.wdgOptions.items():
            if 'chk' in items:
                cfg[name] = items['chk'].get_val()
            elif 'spb' in items:
                cfg[name] = utl.auto_convert(items['spb'].get_val())
        return cfg

    def _cfg_to_ui(self):
        """Update the config information to the UI."""
        for target in self.cfg['input_paths']:
            self.lsvInput.add_item(target, unique=True)
        self.txtPath.set_val(self.cfg['output_path'])
        self.txtSubpath.set_val(self.cfg['output_subpath'])
        self.save_on_exit.set(self.cfg['save_on_exit'])
        self.style.theme_use(self.cfg['gui_style_tk'])
        for name, items in self.wdgModules.items():
            items['chk'].set_val(True if self.cfg[name] else False)
            items['ent'].set_val(self.cfg[name])
        for name, items in self.wdgOptions.items():
            if 'chk' in items:
                items['chk'].set_val(self.cfg[name])
            elif 'spb' in items:
                items['spb'].set_val(self.cfg[name])
        self.activateModules()

    def _make_menu(self):
        self.save_on_exit = pytk.utils.tk.BooleanVar(
            value=self.cfg['save_on_exit'])

        self.mnuMain = pytk.widgets.Menu(self.parent, tearoff=False)
        self.parent.config(menu=self.mnuMain)
        self.mnuFile = pytk.widgets.Menu(self.mnuMain, tearoff=False)
        self.mnuMain.add_cascade(label='File', menu=self.mnuFile)
        self.mnuFileInput = pytk.widgets.Menu(self.mnuFile, tearoff=False)
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
        self.mnuFileOutput = pytk.widgets.Menu(self.mnuFile, tearoff=False)
        self.mnuFile.add_cascade(label='Output', menu=self.mnuFileOutput)
        self.mnuFileOutput.add_command(
            label='Path...', command=self.actionPath)
        self.mnuFile.add_separator()
        self.mnuFile.add_command(label='Run', command=self.actionRun)
        self.mnuFile.add_separator()
        self.mnuFile.add_command(label='Exit', command=self.actionExit)
        self.mnuSettings = pytk.widgets.Menu(self.mnuMain, tearoff=False)
        self.mnuMain.add_cascade(label='Settings', menu=self.mnuSettings)
        self.mnuSettings.add_command(
            label='Advanced', command=self.actionAdvancedSettings)
        self.mnuSettings.add_separator()
        self.mnuSettings.add_command(
            label='Load Settings', command=self.actionLoadSettings)
        self.mnuSettings.add_command(
            label='Save Settings', command=self.actionSaveSettings)
        self.mnuSettings.add_separator()
        self.mnuSettings.add_checkbutton(
            label='Save on Exit', variable=self.save_on_exit)
        self.mnuSettings.add_command(
            label='Reset Defaults', command=self.actionResetDefaults)
        self.mnuHelp = pytk.widgets.Menu(self.mnuMain, tearoff=False)
        self.mnuMain.add_cascade(label='Help', menu=self.mnuHelp)
        self.mnuHelp.add_command(label='About', command=self.actionAbout)

    def actionRun(self, event=None):
        """Action on Click Button Run."""

        def _name_to_tag(text):
            for ending in ('_subpath', '_template'):
                if text.endswith(ending):
                    text = text[:-len(ending)]
            return text

        # TODO: redirect stdout to some log box / use progressbar
        # extract options
        force = self.wdgOptions['force']['chk'].get_val()
        msg('Force: {}'.format(force))
        verbose = VERB_LVL[self.wdgOptions['verbose']['spb'].get_val()]
        msg('Verb.: {}'.format(verbose))
        if self.cfg['use_mp']:
            # parallel
            pool = multiprocessing.Pool(processes=self.cfg['num_processes'])
            proc_results = []
        in_dirpaths = self.lsvInput.get_items()
        for in_dirpath in in_dirpaths:
            kws = {
                name: info['ent'].get_val()
                for name, info in self.wdgModules.items()}
            triggered = collections.OrderedDict(
                [(_name_to_tag(name), ACTIONS[_name_to_tag(name)])
                 for name, info in self.wdgModules.items()
                 if info['chk'].get_val() and _name_to_tag(name) in ACTIONS])
            kws.update({
                'in_dirpath': in_dirpath,
                'out_dirpath': os.path.expanduser(self.txtPath.get()),
                'subpath': self.txtSubpath.get(),
                'actions': triggered,
                'force': force,
                'verbose': verbose,
            })
            if self.cfg['use_mp']:
                proc_results.append(pool.apply_async(dcmpi_run, kwds=kws))
            else:
                dcmpi_run(**kws)
        # print(proc_results)
        if self.cfg['use_mp']:
            res_list = [proc_result.get() for proc_result in proc_results]
        return

    def actionImport(self, event=None):
        """Action on Click Button Import."""
        title = '{} {} List'.format(
            self.btnImport.cget('text'), self.lblInput.cget('text'))
        in_filepath = filedialog.askopenfilename(
            parent=self, title=title, defaultextension='.json',
            initialdir=self.cfg['import_path'],
            filetypes=[('JSON Files', '*.json')])
        if in_filepath:
            try:
                with open(in_filepath, 'r') as in_file:
                    targets = json.load(in_file)
                for target in targets:
                    self.lsvInput.add_item(target, unique=True)
            except ValueError:
                title = self.btnImport.cget('text') + ' Failed'
                msg = 'Could not import input list from `{}`'.format(
                    in_filepath)
                messagebox.showerror(title=title, message=msg)
            finally:
                self.cfg['import_path'] = os.path.dirname(in_filepath)

    def actionExport(self, event=None):
        """Action on Click Button Export."""
        title = '{} {} List'.format(
            self.btnExport.cget('text'), self.lblInput.cget('text'))
        out_filepath = filedialog.asksaveasfilename(
            parent=self, title=title, defaultextension='.json',
            initialdir=self.cfg['export_path'],
            filetypes=[('JSON Files', '*.json')], confirmoverwrite=True)
        if out_filepath:
            targets = self.lsvInput.get_items()
            if not targets:
                title = self.btnExport.cget('text')
                msg = 'Empty {} list.\n'.format(self.lblInput.cget('text')) + \
                      'Do you want to proceed exporting?'
                proceed = messagebox.askyesno(title=title, message=msg)
            else:
                proceed = True
            if proceed:
                with open(out_filepath, 'w') as out_file:
                    json.dump(targets, out_file, sort_keys=True, indent=4)
                self.cfg['export_path'] = os.path.dirname(out_filepath)

    def actionAdd(self, event=None):
        """Action on Click Button Add."""
        title = self.btnAdd.cget('text') + ' ' + self.lblInput.cget('text')
        target = filedialog.askdirectory(
            parent=self, title=title, initialdir=self.cfg['add_path'],
            mustexist=True)
        if target:
            self.lsvInput.add_item(target, unique=True)
            self.cfg['add_path'] = target
            # : adding multiple files
            # for subdir in os.listdir(target):
            #     tmp = os.path.join(target, subdir)
            #     self.lsvInput.add_item(tmp, unique=True)
            # self.cfg['add_path'] = target
        return target

    def actionRemove(self, event=None):
        """Action on Click Button Remove."""
        items = self.lsvInput.get_children('')
        selected = self.lsvInput.selection()
        if selected:
            for item in selected:
                self.lsvInput.delete(item)
        elif items:
            self.lsvInput.delete(items[-1])
        else:
            msg('Empty input list!')

    def actionClear(self, event=None):
        """Action on Click Button Clear."""
        self.lsvInput.clear()

    def actionPath(self, event=None):
        """Action on Click Text Output."""
        title = self.lblOutput.cget('text') + ' ' + self.lblPath.cget('text')
        target = filedialog.askdirectory(
            parent=self, title=title, initialdir=self.cfg['output_path'],
            mustexist=True)
        if target:
            self.txtPath.set_val(target)
        return target

    def activateModules(self, event=None):
        """Action on Change Checkbox Import."""
        for name, items in self.wdgModules.items():
            active = items['chk'].get_val()
            if items['ent']:
                items['ent']['state'] = 'enabled' if active else 'disabled'

    def actionExit(self, event=None):
        """Action on Exit."""
        if messagebox.askokcancel('Quit', 'Are you sure you want to quit?'):
            self.cfg = self._ui_to_cfg()
            if self.cfg['save_on_exit']:
                save_config(self.cfg, self.cfg_filepath)
            self.parent.destroy()

    def actionAbout(self, event=None):
        """Action on About."""
        self.winAbout = About(self.parent)

    def actionAdvancedSettings(self, event=None):
        self.winSettings = Settings(self.parent, self)
        if self.winSettings.result:
            self.cfg.update(self.winSettings.result)
        self._cfg_to_ui()
        # force resize for redrawing widgets correctly
        # w, h = self.parent.winfo_width(), self.parent.winfo_height()
        self.parent.update()

    def actionLoadSettings(self):
        self.cfg = load_config(self.cfg_filepath)
        self._cfg_to_ui()

    def actionSaveSettings(self):
        self.cfg = self._ui_to_cfg()
        save_config(self.cfg, self.cfg_filepath)

    def actionResetDefaults(self, event=None):
        self.cfg = default_config()
        self._cfg_to_ui()


# ======================================================================
def dcmpi_run_gui(*args, **kwargs):
    root = pytk.tk.Tk()
    app = Main(root, *args, **kwargs)
    pytk.utils.set_icon(root, 'icon', DIRS['data'])
    root.mainloop()


# ======================================================================
def dcmpi_run_tui(*args, **kwargs):
    try:
        import asciimatics
    except ImportError:
        asciimatics = None
    # check if asciimatics is available
    # if not asciimatics:
    warnings.warn('Text UI not supported. Using command-line interface...')
    dcmpi_run_cli(**kwargs)
    # else:
    #     pass


# ======================================================================
def dcmpi_run_cli(*args, **kwargs):
    msg('We-are-doomed...')
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
        'ui_mode',
        nargs='?',
        default='tui',
        help='set UI mode [%(default)s]')
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
        '-s', '--subpath',
        default=utl.TPL['acquire'],
        help='Append DICOM-generated subpath to output [%(default)s]')
    arg_parser.add_argument(
        '-n', '--niz_subpath',
        default=utl.ID['niz'],
        help='Sub-path for NIfTI extraction. Empty to skip [%(default)s]')
    arg_parser.add_argument(
        '-m', '--meta_subpath',
        default=utl.ID['meta'],
        help='Sub-path for META extraction. Empty to skip [%(default)s]')
    arg_parser.add_argument(
        '-p', '--prot_subpath',
        default=utl.ID['prot'],
        help='Sub-path for PROT extraction. Empty to skip [%(default)s]')
    arg_parser.add_argument(
        '-t', '--info_subpath',
        default=utl.ID['info'],
        help='Sub-path for INFO extraction. Empty to skip [%(default)s]')
    arg_parser.add_argument(
        '-r', '--report_subpath',
        default=utl.TPL['report'],
        help='Template for the report filename. Empty to skip [%(default)s]')
    arg_parser.add_argument(
        '-b', '--backup_subpath',
        default=utl.TPL['backup'],
        help='Template for the backup filename. Empty to skip [%(default)s]')
    arg_parser.add_argument(
        '-c', '--config', metavar='FILE',
        default=CFG_FILENAME,
        help='specify configuration file name/path [%(default)s]')
    return arg_parser


# ======================================================================
def main_gui():
    """Entry point for Graphical User Interface (GUI)"""
    # this is used by the setup.py script
    main('gui')


# ======================================================================
def main_tui():
    """Entry point for Text User Interface (TUI)"""
    # this is used by the setup.py script
    main('tui')


# ======================================================================
def main_cli():
    """Entry point for Command-Line Interface (CLI)"""
    # this is used by the setup.py script
    main('cli')


# ======================================================================
def main(ui_mode=None):
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

    if not ui_mode:
        ui_mode = args.ui_mode

    if utl.has_graphics(ui_mode):
        dcmpi_run_gui(args)
    elif utl.has_term(ui_mode):
        dcmpi_run_tui(args)
    else:
        dcmpi_run_cli(args)

    exec_time = datetime.datetime.now() - begin_time
    msg('ExecTime: {}'.format(exec_time), args.verbose, VERB_LVL['debug'])


# ======================================================================
if __name__ == '__main__':
    main()
