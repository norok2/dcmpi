#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DCMPI: Monitor folder for creation of new DICOM folder.
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
from __future__ import unicode_literals

# ======================================================================
# :: Python Standard Library Imports
import os  # Miscellaneous operating system interfaces
import random  # Generate pseudo-random numbers
import time  # Time access and conversions
import datetime  # Basic date and time types
import argparse  # Parser for command-line options, arguments and sub-commands
import subprocess  # Subprocess management
import blessed  # Wrapper for terminal coloring, styling, and positioning

# :: External Imports

# :: External Imports Submodules

# :: Local Imports
import dcmpi.utils as utl
from dcmpi import INFO, DIRS
from dcmpi import VERB_LVL, D_VERB_LVL, VERB_LVL_NAMES
from dcmpi import msg, dbg


# ======================================================================
def monitor_folder(
        cmd,
        dirpath,
        delay,
        check,
        on_added=True,
        max_count=0,
        delay_variance=0,
        force=False,
        verbose=D_VERB_LVL):
    """
    Monitor changes in a dir and execute a command upon verify some condition.
    """

    def list_dirs(dirpath):
        return [d for d in os.listdir(dirpath)
                if os.path.isdir(os.path.join(dirpath, d))]

    sec_in_min = 60

    loop = True
    count = 0
    old_dirs = list_dirs(dirpath)
    msg('Watch: {}'.format(dirpath))
    while loop:
        new_dirs = list_dirs(dirpath)
        removed_dirs = [d for d in old_dirs if d not in new_dirs]
        added_dirs = [d for d in new_dirs if d not in old_dirs]
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S %Z', time.localtime())
        randomized = random.random() * delay * delay_variance / 100
        sleep_delay = (delay + randomized) * sec_in_min
        if removed_dirs:
            msg(': {}  --  {}'.format(timestamp, removed_dirs),
                fmt='{t.red}{t.bold}')
        if added_dirs:
            msg(': {}  ++  {}'.format(timestamp, added_dirs),
                fmt='{t.green}{t.bold}')
        if not removed_dirs and not added_dirs:
            text = 'All quiet on the western front.'
            next_check = time.strftime(
                '%H:%M:%S', time.localtime(time.time() + sleep_delay))
            msg(': {}  ..  {}  (next check in ~{} min, at {})'.format(
                timestamp, text, int(delay + randomized), next_check))
        delta_dirs = added_dirs if on_added else removed_dirs
        for delta in delta_dirs:
            delta_dirpath = os.path.join(dirpath, delta)
            if check and check(delta_dirpath):
                cmd = cmd.format(delta_dirpath)
                subprocess.call(cmd, shell=True)
                count += 1
        time.sleep(sleep_delay)
        if 0 < max_count < count:
            loop = False
        else:
            old_dirs = new_dirs
            loop = True


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
        '-d', '--dir', metavar='DIR',
        default='.',
        help='set working directory [%(default)s]')
    arg_parser.add_argument(
        '-l', '--delay', metavar='X',
        type=float, default=60.0,
        help='set checking interval in min [%(default)s]')
    arg_parser.add_argument(
        '-r', '--delay_var', metavar='DX',
        type=float, default=5,
        help='set random variance in the delay as percentage [%(default)s]')
    arg_parser.add_argument(
        '-m', '--max_count', metavar='NUM',
        type=int, default=0,
        help='maximum number of actions to be performed [%(default)s]')
    arg_parser.add_argument(
        '-c', '--cmd', metavar='EXECUTABLE',
        default=os.path.dirname(__file__) + '/dcm_analyze_dir.py {}',
        help='execute when finding a new dir with DICOMs [%(default)s]')
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

    monitor_folder(
        args.cmd,
        args.dir, args.delay,
        lambda x: utl.find_a_dicom(x)[0],
        True,
        args.max_count, args.delay_var,
        args.force, args.verbose)

    exec_time = datetime.datetime.now() - begin_time
    msg('ExecTime: {}'.format(exec_time), args.verbose, VERB_LVL['debug'])


# ======================================================================
if __name__ == '__main__':
    main()
