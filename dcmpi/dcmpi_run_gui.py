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

# :: External Imports
import pytk

# :: External Imports Submodules
import pytk.widgets

# :: Local Imports
import dcmpi.utils as utl
from dcmpi import INFO, DIRS
from dcmpi import VERB_LVL, D_VERB_LVL, VERB_LVL_NAMES
from dcmpi import msg, dbg
from dcmpi import MY_GREETINGS

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
        'import_subpath': utl.ID['dicom'],
        'niz_subpath': utl.ID['niz'],
        'meta_subpath': utl.ID['meta'],
        'prot_subpath': utl.ID['prot'],
        'info_subpath': utl.ID['info'],
        'report_template': utl.TPL['report'],
        'backup_template': utl.TPL['backup'],
        'force': False,
        'verbose': D_VERB_LVL,
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
        import_subpath=utl.ID['dicom'],
        niz_subpath=utl.ID['niz'],
        meta_subpath=utl.ID['meta'],
        prot_subpath=utl.ID['prot'],
        info_subpath=utl.ID['info'],
        report_template=utl.TPL['report'],
        backup_template=utl.TPL['backup'],
        force=False,
        verbose=D_VERB_LVL):
    """
    Standard preprocessing of DICOM files.

    Args:
        in_dirpath (str): Path to input directory.
        out_dirpath (str): Path to output directory.
        subpath ():
        niz_subpath ():
        meta_subpath ():
        prot_subpath ():
        info_subpath ():
        report_subpath ():
        backup_subpath ():
        force (bool): Force new processing.
        verbose (int): Set level of verbosity.

    Returns:
        None.
    """
    from dcmpi.do_acquire_sources import do_acquire_sources
    from dcmpi.do_sorting import sorting

    subdirs = (
        niz_subpath, meta_subpath, prot_subpath, info_subpath, report_template,
        backup_template)
    # import
    dcm_dirpaths = do_acquire_sources(
        in_dirpath, out_dirpath, 'copy', subpath, import_subpath,
        force, verbose)
    for dcm_dirpath in dcm_dirpaths:
        base_dirpath = os.path.dirname(dcm_dirpath)
        # sort
        sorting(
            dcm_dirpath, utl.D_SUMMARY + '.' + utl.EXT['json'],
            force, verbose)
        msg('Done: {}'.format(dcm_dirpath))


# ======================================================================
def get_curr_screen_geometry():
    """
    Workaround to get the size of the current screen in a multi-screen setup.

    Returns:
        geometry (str): The standard Tk geometry string.
            [width]x[height]+[left]+[top]
    """
    temp = tk.Tk()
    temp.update()
    temp.attributes('-fullscreen', True)
    temp.state('iconic')
    geometry = temp.winfo_geometry()
    temp.destroy()
    return geometry


# ======================================================================
def center(target, parent=None):
    target.update_idletasks()
    if parent is None:
        parent_geom = Geometry(get_curr_screen_geometry())
    else:
        parent.update_idletasks()
        parent_geom = Geometry(parent.winfo_geometry())
    target_geom = Geometry(target.winfo_geometry()).set_to_center(parent_geom)
    target.geometry(target_geom.as_str())


# ======================================================================
class Geometry():
    def __init__(self, geometry_text=None):
        """
        Generate a geometry object from the standard Tk geometry string.

        Args:
            geometry_text (str): The standard Tk geometry string.
                [width]x[height]+[left]+[top]

        Returns:
            None.
        """
        try:
            tokens1 = geometry_text.split('+')
            tokens2 = tokens1[0].split('x')
            self.width = int(tokens2[0])
            self.height = int(tokens2[1])
            self.left = int(tokens1[1])
            self.top = int(tokens1[2])
        except:
            self.width, self.height, self.left, self.top = 0, 0, 0, 0

    def __repr__(self):
        return self.as_str()

    def as_dict(self):
        return {
            'w': self.width,
            'h': self.height,
            'l': self.left,
            't': self.top}

    def as_tuple(self):
        return self.width, self.height, self.left, self.top

    def as_str(self):
        return '{w:d}x{h:d}+{l:d}+{t:d}'.format(**self.as_dict())

    def set_to_center(self, parent):
        """
        Update the geometry to be centered with respect to a container.

        Args:
            parent (Geometry): The geometry of the container.

        Returns:
            geometry (Geometry): The updated geometry.
        """
        self.left = parent.width // 2 - self.width // 2 + parent.left
        self.top = parent.height // 2 - self.height // 2 + parent.top
        return self

    def set_to_origin(self):
        """
        Update the geometry to be centered with respect to a container.

        Args:
            parent (Geometry): The geometry of the container.

        Returns:
            geometry (Geometry): The updated geometry.
        """
        self.left = 0
        self.top = 0
        return self

    def set_to_top_left(self, parent):
        """
        Update the geometry to be centered with respect to a container.

        Args:
            parent (Geometry): The geometry of the container.

        Returns:
            geometry (Geometry): The updated geometry.
        """
        self.left = parent.left
        self.top = parent.top
        return self

    def set_to_top(self, parent):
        """
        Update the geometry to be centered with respect to a container.

        Args:
            parent (Geometry): The geometry of the container.

        Returns:
            geometry (Geometry): The updated geometry.
        """
        self.left = parent.width // 2 - self.width // 2 + parent.left
        self.top = parent.top
        return self

    def set_to_top_right(self, parent):
        """
        Update the geometry to be centered with respect to a container.

        Args:
            parent (Geometry): The geometry of the container.

        Returns:
            geometry (Geometry): The updated geometry.
        """
        self.left = parent.width - self.width + parent.left
        self.top = parent.top
        return self

    def set_to_right(self, parent):
        """
        Update the geometry to be centered with respect to a container.

        Args:
            parent (Geometry): The geometry of the container.

        Returns:
            geometry (Geometry): The updated geometry.
        """
        self.left = parent.width - self.width + parent.left
        self.top = parent.height // 2 - self.height // 2 + parent.top
        return self

    def set_to_bottom_right(self, parent):
        """
        Update the geometry to be centered with respect to a container.

        Args:
            parent (Geometry): The geometry of the container.

        Returns:
            geometry (Geometry): The updated geometry.
        """
        self.left = parent.width - self.width + parent.left
        self.top = parent.height - self.height + parent.top
        return self

    def set_to_bottom(self, parent):
        """
        Update the geometry to be centered with respect to a container.

        Args:
            parent (Geometry): The geometry of the container.

        Returns:
            geometry (Geometry): The updated geometry.
        """
        self.left = parent.width // 2 - self.width // 2 + parent.left
        self.top = parent.height - self.height + parent.top
        return self

    def set_to_bottom_left(self, parent):
        """
        Update the geometry to be centered with respect to a container.

        Args:
            parent (Geometry): The geometry of the container.

        Returns:
            geometry (Geometry): The updated geometry.
        """
        self.left = parent.left
        self.top = parent.height - self.height + parent.top
        return self

    def set_to_left(self, parent):
        """
        Update the geometry to be centered with respect to a container.

        Args:
            parent (Geometry): The geometry of the container.

        Returns:
            geometry (Geometry): The updated geometry.
        """
        self.left = parent.left
        self.top = parent.height // 2 - self.height // 2 + parent.top
        return self


# ======================================================================
class Entry(pytk.widgets.Entry):
    def __init__(self, *args, **kwargs):
        pytk.widgets.Entry.__init__(self, *args, **kwargs)

    def get_val(self):
        return self.get()

    def set_val(self, val=''):
        try:
            if val is not None:
                val = str(val)
            else:
                raise ValueError
        except ValueError:
            val = ''
        state = self['state']
        self['state'] = 'enabled'
        self.delete(0, tk.END)
        self.insert(0, val)
        self['state'] = state


# ======================================================================
class Checkbutton(pytk.widgets.Checkbutton):
    def __init__(self, *args, **kwargs):
        pytk.widgets.Checkbutton.__init__(self, *args, **kwargs)

    def get_val(self):
        return 'selected' in self.state()

    def set_val(self, val=True):
        # if (val and not self.get_val()) or (not val and self.get_val()):
        if bool(val) ^ bool(self.get_val()):  # bitwise xor
            self.toggle()

    def toggle(self):
        self.invoke()


# ======================================================================
class Spinbox(tk.Spinbox):
    def __init__(self, *args, **kwargs):
        if 'start' in kwargs:
            kwargs['from_'] = kwargs.pop('start')
        if 'stop' in kwargs:
            kwargs['to'] = kwargs.pop('stop')
        if 'step' in kwargs:
            kwargs['increment'] = kwargs.pop('step')
        tk.Spinbox.__init__(self, *args, **kwargs)
        self.values = kwargs['values'] if 'values' in kwargs else None
        self.start = kwargs['from_'] if 'from_' in kwargs else None
        self.stop = kwargs['to'] if 'to' in kwargs else None
        self.step = kwargs['increment'] if 'increment' in kwargs else None
        self.bind('<MouseWheel>', self.mouseWheel)
        self.bind('<Button-4>', self.mouseWheel)
        self.bind('<Button-5>', self.mouseWheel)
        self.sys_events = {
            'scroll_up': {'unix': 4, 'win': +120},
            'scroll_down': {'unix': 5, 'win': -120}}

    def mouseWheel(self, event):
        scroll_up = (
            event.num == self.sys_events['scroll_up']['unix'] or
            event.delta == self.sys_events['scroll_up']['win'])
        scroll_down = (
            event.num == self.sys_events['scroll_down']['unix'] or
            event.delta == self.sys_events['scroll_down']['win'])
        if scroll_up:
            self.invoke('buttonup')
        elif scroll_down:
            self.invoke('buttondown')

    def is_valid(self, val=''):
        if self.values:
            result = self.get_val() in self.values
        else:
            result = self.start <= self.get_val() <= self.stop
        return result

    def get_val(self):
        return utl.auto_convert(self.get())

    def set_val(self, val=''):
        if self.is_valid(val):
            state = self['state']
            self['state'] = 'normal'
            self.delete(0, tk.END)
            self.insert(0, val)
            self['state'] = state
        else:
            raise ValueError('Spinbox: value `{}` not allowed.'.format(val))


# ======================================================================
class Listbox(pytk.widgets.Combobox):
    def __init__(self, *args, **kwargs):
        pytk.widgets.Combobox.__init__(self, *args, **kwargs)
        self['state'] = 'readonly'

    def get_values(self):
        return self.configure('values')[-1]

    def get_val(self):
        return self.get()

    def set_val(self, val=''):
        self.set(val)


# ======================================================================
class Listview(pytk.widgets.Treeview):
    def __init__(self, *args, **kwargs):
        pytk.widgets.Treeview.__init__(self, *args, **kwargs)

    def get_items(self):
        return [self.item(child, 'text') for child in self.get_children('')]

    def add_item(self, item, unique=False):
        items = self.get_items()
        if not unique or unique and item not in items:
            self.insert('', tk.END, text=item)

    def del_item(self, item):
        for child in self.get_children(''):
            if self.item(child, 'text') == item:
                self.delete(child)

    def clear(self):
        for child in self.get_children(''):
            self.delete(child)


# ======================================================================
class About(tk.Toplevel):
    def __init__(self, parent):
        self.win = tk.Toplevel.__init__(self, parent)
        self.transient(parent)
        self.parent = parent
        self.title('About {}'.format(INFO['name']))
        self.resizable(False, False)
        self.frm = pytk.widgets.Frame(self)
        self.frm.pack(fill=tk.BOTH, expand=True)
        self.frmMain = pytk.widgets.Frame(self.frm)
        self.frmMain.pack(fill=tk.BOTH, padx=1, pady=1, expand=True)

        about_txt = '\n'.join((
            MY_GREETINGS[1:],
            'DCMPI: DICOM Preprocess Interface',
            __doc__,
            '{} - ver. {}\n{} {}\n{}'.format(
                INFO['name'], INFO['version'],
                INFO['copyright'], INFO['author'], INFO['notice'])
        ))
        msg(about_txt)
        self.lblInfo = pytk.widgets.Label(
            self.frmMain, text=about_txt, anchor=tk.CENTER,
            background='#333', foreground='#ccc', font='TkFixedFont')
        self.lblInfo.pack(padx=8, pady=8, ipadx=8, ipady=8)

        self.btnClose = pytk.widgets.Button(
            self.frmMain, text='Close', command=self.destroy)
        self.btnClose.pack(side=tk.BOTTOM, padx=8, pady=8)
        self.bind('<Return>', self.destroy)
        self.bind('<Escape>', self.destroy)

        center(self, self.parent)

        self.grab_set()
        self.wait_window(self)


# ======================================================================
class Settings(tk.Toplevel):
    def __init__(self, parent, app):
        self.settings = collections.OrderedDict((
            ('use_mp', {'label': 'Use parallel processing', 'dtype': bool,}),
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

        self.win = tk.Toplevel.__init__(self, parent)
        self.transient(parent)
        self.parent = parent
        self.app = app
        self.title('{} Advanced Settings'.format(INFO['name']))
        self.frm = pytk.widgets.Frame(self)
        self.frm.pack(fill=tk.BOTH, expand=True)
        self.frmMain = pytk.widgets.Frame(self.frm)
        self.frmMain.pack(fill=tk.BOTH, padx=8, pady=8, expand=True)

        self.frmSpacers = []

        self.wdgOptions = {}
        for name, info in self.settings.items():
            if info['dtype'] == bool:
                chk = Checkbutton(self.frmMain, text=info['label'])
                chk.pack(fill=tk.X, padx=1, pady=1)
                chk.set_val(info['default'])
                self.wdgOptions[name] = {'chk': chk}
            elif info['dtype'] == int:
                frm = pytk.widgets.Frame(self.frmMain)
                frm.pack(fill=tk.X, padx=1, pady=1)
                lbl = pytk.widgets.Label(frm, text=info['label'])
                lbl.pack(side=tk.LEFT, fill=tk.X, padx=1, pady=1, expand=True)
                spb = Spinbox(frm, **info['values'])
                spb.set_val(info['default'])
                spb.pack(
                    side=tk.LEFT, fill=tk.X, anchor=tk.W, padx=1, pady=1)
                self.wdgOptions[name] = {'frm': frm, 'lbl': lbl, 'spb': spb}
            elif info['dtype'] == tuple:
                frm = pytk.widgets.Frame(self.frmMain)
                frm.pack(fill=tk.X, padx=1, pady=1)
                lbl = pytk.widgets.Label(frm, text=info['label'])
                lbl.pack(side=tk.LEFT, fill=tk.X, padx=1, pady=1, expand=True)
                lst = Listbox(frm, values=info['values'])
                lst.set_val(info['default'])
                lst.pack(
                    side=tk.LEFT, fill=tk.X, anchor=tk.W, padx=1, pady=1)
                self.wdgOptions[name] = {'frm': frm, 'lbl': lbl, 'lst': lst}

        self.frmButtons = pytk.widgets.Frame(self.frmMain)
        self.frmButtons.pack(side=tk.BOTTOM, padx=4, pady=4)
        spacer = pytk.widgets.Frame(self.frmButtons)
        spacer.pack(side=tk.LEFT, anchor='e', expand=True)
        self.frmSpacers.append(spacer)
        self.btnOK = pytk.widgets.Button(
            self.frmButtons, text='OK', compound=tk.LEFT,
            command=self.ok)
        self.btnOK.pack(side=tk.LEFT, padx=4, pady=4)
        self.btnReset = pytk.widgets.Button(
            self.frmButtons, text='Reset', compound=tk.LEFT,
            command=self.reset)
        self.btnReset.pack(side=tk.LEFT, padx=4, pady=4)
        self.btnCancel = pytk.widgets.Button(
            self.frmButtons, text='Cancel', compound=tk.LEFT,
            command=self.cancel)
        self.btnCancel.pack(side=tk.LEFT, padx=4, pady=4)
        self.bind('<Return>', self.ok)
        self.bind('<Escape>', self.cancel)

        center(self, self.parent)

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
class MainGui(pytk.widgets.Frame):
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
            ('import_subpath', {'label': 'DICOM'}),
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

        self.style = pytk.widgets.Style()
        # print(self.style.theme_names())
        self.style.theme_use(self.cfg['gui_style_tk'])
        self.pack(fill=tk.BOTH, expand=True)

        self._make_menu()

        # :: define UI items
        self.frmMain = pytk.widgets.Frame(self)
        self.frmMain.pack(fill=tk.BOTH, padx=8, pady=8, expand=True)
        self.frmSpacers = []

        # left frame
        self.frmLeft = pytk.widgets.Frame(self.frmMain)
        self.frmLeft.pack(
            side=tk.LEFT, fill=tk.BOTH, padx=4, pady=4, expand=True)

        self.frmInput = pytk.widgets.Frame(self.frmLeft)
        self.frmInput.pack(
            side=tk.TOP, fill=tk.BOTH, padx=4, pady=4, expand=True)
        self.lblInput = pytk.widgets.Label(self.frmInput, text='Input')
        self.lblInput.pack(padx=1, pady=1)
        self.lsvInput = Listview(self.frmInput, show='tree', height=4)
        self.lsvInput.bind('<Double-Button-1>', self.actionAdd)
        self.lsvInput.pack(fill=tk.BOTH, padx=1, pady=1, expand=True)
        self.btnImport = pytk.widgets.Button(
            self.frmInput, text='Import', compound=tk.LEFT,
            command=self.actionImport)
        self.btnImport.pack(side=tk.LEFT, padx=4, pady=4)
        self.btnExport = pytk.widgets.Button(
            self.frmInput, text='Export', compound=tk.LEFT,
            command=self.actionExport)
        self.btnExport.pack(side=tk.LEFT, padx=4, pady=4)
        spacer = pytk.widgets.Frame(self.frmInput)
        spacer.pack(side=tk.LEFT, anchor='e', expand=True)
        self.frmSpacers.append(spacer)
        self.btnAdd = pytk.widgets.Button(
            self.frmInput, text='Add', compound=tk.LEFT,
            command=self.actionAdd)
        self.btnAdd.pack(side=tk.LEFT, anchor='e', padx=4, pady=4)
        self.btnRemove = pytk.widgets.Button(
            self.frmInput, text='Remove', compound=tk.LEFT,
            command=self.actionRemove)
        self.btnRemove.pack(side=tk.LEFT, anchor='e', padx=4, pady=4)
        self.btnClear = pytk.widgets.Button(
            self.frmInput, text='Clear', compound=tk.LEFT,
            command=self.actionClear)
        self.btnClear.pack(side=tk.LEFT, anchor='e', padx=4, pady=4)

        self.frmOutput = pytk.widgets.Frame(self.frmLeft)
        self.frmOutput.pack(fill=tk.X, padx=4, pady=4)
        self.lblOutput = pytk.widgets.Label(self.frmOutput, text='Output')
        self.lblOutput.pack(side=tk.TOP, padx=1, pady=1)

        self.frmPath = pytk.widgets.Frame(self.frmOutput)
        self.frmPath.pack(fill=tk.X, expand=True)
        self.lblPath = pytk.widgets.Label(self.frmPath, text='Path', width=8)
        self.lblPath.pack(side=tk.LEFT, fill=tk.X, padx=1, pady=1)
        self.entPath = Entry(self.frmPath)
        self.entPath.insert(0, self.cfg['output_path'])
        self.entPath.bind('<Double-Button>', self.actionPath)
        self.entPath.pack(
            side=tk.LEFT, fill=tk.X, padx=1, pady=1, expand=True)

        self.frmSubpath = pytk.widgets.Frame(self.frmOutput)
        self.frmSubpath.pack(fill=tk.X, expand=True)
        self.lblSubpath = pytk.widgets.Label(self.frmSubpath, text='Sub-Path', width=8)
        self.lblSubpath.pack(side=tk.LEFT, fill=tk.X, padx=1, pady=1)
        self.entSubpath = Entry(self.frmSubpath)
        self.entSubpath.insert(0, self.cfg['output_subpath'])
        self.entSubpath.pack(
            side=tk.LEFT, fill=tk.X, padx=1, pady=1, expand=True)

        # right frame
        self.frmRight = pytk.widgets.Frame(self.frmMain)
        self.frmRight.pack(side=tk.RIGHT, fill=tk.BOTH, padx=4, pady=4)

        self.lblActions = pytk.widgets.Label(
            self.frmRight, text='Sub-Paths and Templates')
        self.lblActions.pack(padx=1, pady=1)
        self.wdgModules = {}
        for name, info in self.modules.items():
            frm = pytk.widgets.Frame(self.frmRight)
            frm.pack(fill=tk.X, padx=1, pady=1)
            if 'subpath' in name:
                chk = Checkbutton(frm, text=info['label'])
                chk.pack(
                    side=tk.LEFT, fill=tk.X, padx=1, pady=1, expand=True)
                chk.config(command=self.activateModules)
                entry = Entry(frm, width=8)
                entry.pack(side=tk.RIGHT, fill=tk.X, padx=1, pady=1)
            elif 'template' in name:
                chk = Checkbutton(frm, text=info['label'])
                chk.pack(fill=tk.X, padx=1, pady=1, expand=True)
                # chk.set_val(info['default'])
                chk.config(command=self.activateModules)
                entry = Entry(frm, width=24)
                entry.pack(fill=tk.X, padx=1, pady=1, expand=True)
            else:
                chk = Checkbutton(frm, text=info['label'])
                chk.pack(fill=tk.X, padx=1, pady=1, expand=True)
                chk.config(command=self.activateModules)
                entry = None
            self.wdgModules[name] = {
                'frm': frm, 'chk': chk, 'ent': entry}
        self.activateModules()

        spacer = pytk.widgets.Frame(self.frmRight)
        spacer.pack(side=tk.TOP, padx=4, pady=4)
        self.frmSpacers.append(spacer)
        self.lblOptions = pytk.widgets.Label(self.frmRight, text='Options')
        self.lblOptions.pack(padx=1, pady=1)
        self.wdgOptions = {}
        for name, info in self.options.items():
            if info['dtype'] == bool:
                chk = Checkbutton(self.frmRight, text=info['label'])
                chk.pack(fill=tk.X, padx=1, pady=1)
                self.wdgOptions[name] = {'chk': chk}
            elif info['dtype'] == int:
                frm = pytk.widgets.Frame(self.frmRight)
                frm.pack(fill=tk.X, padx=1, pady=1)
                lbl = pytk.widgets.Label(frm, text=info['label'])
                lbl.pack(side=tk.LEFT, fill=tk.X, padx=1, pady=1)
                spb = Spinbox(frm, **info['values'])
                spb.pack(
                    side=tk.LEFT, fill=tk.X, anchor=tk.W, padx=1, pady=1)
                self.wdgOptions[name] = {'frm': frm, 'lbl': lbl, 'spb': spb}
            elif info['dtype'] == str:
                pass

        # spacer = pytk.widgets.Frame(self.frmRight)
        # spacer.pack(side=tk.TOP, padx=4, pady=4)
        # self.frmSpacers.append(spacer)
        # self.pbrRunning = pytk.widgets.Progressbar(self.frmRight)
        # self.pbrRunning.pack(side=tk.TOP, fill=tk.X, expand=True)

        spacer = pytk.widgets.Frame(self.frmRight)
        spacer.pack(side=tk.TOP, padx=4, pady=4)
        self.frmSpacers.append(spacer)
        self.frmButtons = pytk.widgets.Frame(self.frmRight)
        self.frmButtons.pack(side=tk.BOTTOM, padx=4, pady=4)
        spacer = pytk.widgets.Frame(self.frmButtons)
        spacer.pack(side=tk.LEFT, anchor='e', expand=True)
        self.frmSpacers.append(spacer)
        self.btnRun = pytk.widgets.Button(
            self.frmButtons, text='Run', compound=tk.LEFT,
            command=self.actionRun)
        self.btnRun.pack(side=tk.LEFT, padx=4, pady=4)
        self.btnExit = pytk.widgets.Button(
            self.frmButtons, text='Exit', compound=tk.LEFT,
            command=self.actionExit)
        self.btnExit.pack(side=tk.LEFT, padx=4, pady=4)

        center(self.parent)

        self._cfg_to_ui()

    # --------------------------------
    def _ui_to_cfg(self):
        """Update the config information from the UI."""
        cfg = self.cfg
        cfg.update({
            'input_paths': self.lsvInput.get_items(),
            'output_path': self.entPath.get(),
            'output_subpath': self.entSubpath.get(),
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
        self.entPath.set_val(self.cfg['output_path'])
        self.entSubpath.set_val(self.cfg['output_subpath'])
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
        self.save_on_exit = tk.BooleanVar(value=self.cfg['save_on_exit'])

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
        self.mnuFile.add_command(label='Exit', command=self.actionExit)
        self.mnuSettings = tk.Menu(self.mnuMain, tearoff=False)
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
        self.mnuHelp = tk.Menu(self.mnuMain, tearoff=False)
        self.mnuMain.add_cascade(label='Help', menu=self.mnuHelp)
        self.mnuHelp.add_command(label='About', command=self.actionAbout)

    def actionRun(self, event=None):
        """Action on Click Button Run."""
        # TODO: redirect stdout to some log box / use progressbar
        # extract options
        force = self.wdgOptions['force']['chk'].get_val()
        msg('Force: {}'.format(force))
        verbose = VERB_LVL[self.wdgOptions['verbose']['spb'].get_val()]
        msg('Verb.: {}'.format(verbose))
        if self.cfg['use_mp']:
            # parallel
            pool = multiprocessing.Pool(processes=self.cfg['num_processes'])
            proc_result_list = []
        for in_dirpath in self.lsvInput.get_items():
            kws = {
                name: info['ent'].get_val()
                for name, info in self.wdgModules.items()}
            kws.update({
                'in_dirpath': in_dirpath,
                'out_dirpath': os.path.expanduser(self.entPath.get()),
                'subpath': self.entSubpath.get(),
                'force': force,
                'verbose': verbose,
            })
            # print(kws)
            if self.cfg['use_mp']:
                proc_result = pool.apply_async(
                    dcmpi_run, kwds=kws)
                proc_result_list.append(proc_result)
            else:
                dcmpi_run(**kws)
        # print(proc_result_list)
        if self.cfg['use_mp']:
            res_list = []
            for proc_result in proc_result_list:
                res_list.append(proc_result.get())
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
            self.entPath.set_val(target)
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
    root = tk.Tk()
    app = MainGui(root, *args, **kwargs)
    root.mainloop()
