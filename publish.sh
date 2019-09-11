#!/bin/bash

rm -rf build dist d2yabt.egg-info/

python3 setup.py sdist bdist_wheel || exit 1

python3 -m twine upload --verbose --repository-url https://upload.pypi.org/legacy/ dist/*

