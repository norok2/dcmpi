#!/bin/sh
#python fix_version.py
python setup.py bdist_wheel --universal
twine upload dist/* --config-file .pypirc
