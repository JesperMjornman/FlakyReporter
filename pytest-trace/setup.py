#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import codecs
from setuptools import setup


def read(fname):
    file_path = os.path.join(os.path.dirname(__file__), fname)
    return codecs.open(file_path, encoding='utf-8').read()


setup(
    name='pytest-trace',
    version='0.1.0',
    author='Jesper Mjörnman & Daniel Mastell',
    author_email='jesmj855@student.liu.se',
    maintainer='Jesper Mjörnman & Daniel Mastell',
    maintainer_email='jesmj855@student.liu.se',
    license='MIT',
    url='https://github.com/JesperMjornman/pytest-pytraceflaky',
    description='A plugin for tracing execution for both passing and failing',
    #long_description=read('README.rst'),
    py_modules=['pytest_trace'],
    python_requires='>=3.6.5',
    setup_requires=['wheel'],
    install_requires=['pytest>=3.10.0'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Pytest',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Testing',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
    ],
    entry_points={
        'pytest11': [
            'flakytrace = pytest_trace',
        ],
    },
)
