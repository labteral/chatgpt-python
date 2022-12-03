#!/bin/bash
python3 setup.py bdist_wheel
twine upload dist/*.whl
