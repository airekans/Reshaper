#! /usr/bin/env python

""" Setup script for reshaper. """

from distutils.core import setup

setup(name='reshaper',
      version='0.1',
      description='C++ refactoring library based on libclang python bindings',
      author='airekans',
      author_email='airekans@gmail.com',
      url='https://github.com/airekans/reshaper',
      packages=['reshaper'],
      scripts=['extract_interface.py', 'ast_dump.py', 
               'tools/cdb_dump.py']
)

