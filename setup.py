#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Setup instructions.

See: https://packaging.python.org/en/latest/distributing.html
"""

from setuptools import setup, find_packages
from codecs import open  # use a consistent encoding (in Python 2)
from dcmpi import __version__ as version_text
import os

cwd = os.path.realpath(os.path.dirname(__file__))

# get the long description from the README file
with open(os.path.join(cwd, 'README'), encoding='utf-8') as readme_file:
    long_description_text = readme_file.read()

setup(
    name='dcmpi',

    description='DICOM Preprocessing Interface.',
    long_description=long_description_text,

    version=version_text,

    url='https://bitbucket.org/norok2/dcmpi',

    author='Riccardo Metere',
    author_email='rick@metere.it',

    license='GPLv3+',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 4 - Beta',

        'Intended Audience :: System Administrators',

        'Topic :: System :: Shells',
        'Topic :: System :: Systems Administration',
        'Topic :: System :: Filesystems',
        'Topic :: System :: Monitoring',
        'Topic :: Utilities',

        'Operating System :: POSIX',

        'License :: OSI Approved :: GNU General Public License v3 or later'
        ' (GPLv3+)',

        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
    ],

    keywords='dicom dcm preprocessing',

    packages=find_packages(exclude=['contrib', 'docs', 'tests']),

    install_requires=['dicom'],

    # package_data={
    #     'license': ['LICENSE'],
    # },

    # data_files=[('my_data', ['data/data_file'])],

    entry_points={
        'console_scripts': [
            'hdu=hdu.hdu:main',
        ],
    },
)
