#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup
from setuptools import find_packages
import chatgpt

setup(
    name='chatgpt',
    version=chatgpt.__version__,
    description='',
    url='https://github.com/brunneis/chatgpt-python',
    author='Rodrigo Martínez Castaño, Alejandro Suárez',
    author_email='rodrigo@martinez.gal, alejandrosuarez.eu@gmail.com',
    license='GNU General Public License v3 (GPLv3)',
    packages=find_packages(),
    zip_safe=False,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.6",
    entry_points={
        'console_scripts': [
            'chatgpt = chatgpt.cli.__main__:main',
        ],
    },
    install_requires=[
        "tls_client",
        "rich"
    ]
)