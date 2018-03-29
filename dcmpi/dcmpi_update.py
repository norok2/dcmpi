#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DCMPI: update information on DICOM files.
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
import shutil  # High-level file operations
import datetime  # Basic date and time types
import argparse  # Parser for command-line options, arguments and sub-commands
import json  # JSON encoder and decoder [JSON: JavaScript Object Notation]

# :: External Imports
import pydicom as pydcm  # PyDicom (Read, modify and write DICOM files.)

# :: External Imports Submodules

# :: Local Imports
import dcmpi.utils as utl
from dcmpi import INFO, DIRS
from dcmpi import VERB_LVL, D_VERB_LVL, VERB_LVL_NAMES
from dcmpi import msg, dbg


# ======================================================================
def dcmpi_update(
        dirpath,
        dcm_info=None,
        backup_prefix='~',
        verbose=D_VERB_LVL):
    """
    Modify selected DICOM fields of files within a directory.

    Args:
        dirpath (str): Path to input directory.
        dcm_info (str): JSON encoded dictionary of DICOM fields to update.
            If None, DICOM files are left untouched.
        backup_prefix (str): Prefix to use for backup files.
        verbose (int): Set level of verbosity.

    Returns:
        None.

    See Also:
        utl.is_dicom, utl.is_compressed_dicom
    """

    def get_filepaths(path):
        for root, dirs, files in os.walk(path):  # no need to sort
            for name in files:
                yield os.path.join(root, name)

    msg(':: Updating DICOMs...')
    msg('Path: {}'.format(os.path.realpath(dirpath)),
        verbose, VERB_LVL['low'])

    if os.path.exists(dirpath) and dcm_info:
        # load DICOM field to update
        dcm_info = json.loads(dcm_info)
        # :: analyze directory tree
        for filepath in get_filepaths(dirpath):
            basepath, filename = os.path.split(filepath)
            msg('Analyzing `{}`...'.format(filepath),
                verbose, VERB_LVL['debug'])
            if backup_prefix:
                backup_filepath = os.path.join(
                    basepath, backup_prefix + filename)
                shutil.copy(filepath, backup_filepath)
                msg('Backup `{}`'.format(backup_filepath),
                    verbose, VERB_LVL['medium'])
            is_dicom = utl.is_dicom(
                filepath,
                allow_dir=False,
                allow_report=True,
                allow_postprocess=True)
            if not is_dicom:
                is_compressed, compression = utl.is_compressed_dicom(
                    filepath,
                    allow_dir=False,
                    allow_report=True,
                    allow_postprocess=True)
            else:
                is_compressed = False
                compression = None
            if is_dicom or is_compressed and compression in utl.COMPRESSIONS:
                if is_compressed and compression in utl.COMPRESSIONS:
                    dcm_filepath = os.path.splitext(filepath)[0]
                    cmd = utl.COMPRESSIONS[compression]['bwd'] + ' {}'.format(
                        filepath)
                    utl.execute(cmd)
                    msg('Uncompressing: `{}`'.format(dcm_filepath),
                        verbose, VERB_LVL['high'])
                else:
                    dcm_filepath = filepath
                try:
                    dcm = pydcm.read_file(dcm_filepath)
                    for key, val in dcm_info.items():
                        if key in dcm:
                            setattr(dcm, key, str(val))
                        else:
                            msg('W: DICOM attr: `` not found.',
                                verbose, VERB_LVL['medium'])
                    dcm.save_as(dcm_filepath)
                except:
                    msg('E: Could not open DICOM: {}.'.format(dcm_filepath))
                finally:
                    if is_compressed and compression in utl.COMPRESSIONS:
                        cmd = utl.COMPRESSIONS[compression]['fwd'] + \
                              ' {}'.format(dcm_filepath)
                        utl.execute(cmd)
                        msg('Compressing: `{}`'.format(filepath),
                            verbose, VERB_LVL['high'])
                    if dcm_filepath != filepath and \
                            os.path.isfile(dcm_filepath):
                        os.remove(dcm_filepath)
            else:
                subpath = filepath[len(dirpath):]
                msg('W: Invalid source found `{}`'.format(subpath),
                    verbose, VERB_LVL['medium'])
    else:
        msg('W: Input path does NOT exists.', verbose, VERB_LVL['low'])


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
        '-d', '--dirpath', metavar='DIR',
        default='.',
        help='set working directory [%(default)s]')
    arg_parser.add_argument(
        '-c', '--dcm_info', metavar='DIR',
        default='{'
                '"PatientID": null, '
                '"PatientBirthDate": null, '
                '"PatientName": null}',
        help='set DICOM fields to update [%(default)s]')
    arg_parser.add_argument(
        '-b', '--backup_prefix',
        default=None,
        help='set prefix to be prepended to backup files [%(default)s]')
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

    dcmpi_update(
        args.dirpath, args.dcm_info, args.backup_prefix, args.verbose)

    exec_time = datetime.datetime.now() - begin_time
    msg('ExecTime: {}'.format(exec_time), args.verbose, VERB_LVL['debug'])


# ======================================================================
if __name__ == '__main__':
    main()
