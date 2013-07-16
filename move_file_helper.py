#!/usr/bin/env python

"""move files helper
this script is used to move files;
if you want to move file A.cpp under libB,
it can find out all files that used(directly or indirectly)
by A.cpp under libB
"""
import os, sys, re
from optparse import OptionParser
from functools import partial
from reshaper.option import setup_options
from reshaper.ast import get_tu
from reshaper.semantic import get_lib_name, get_source_path_candidates
import pdb

class IncludeObject(object):
    def __init__(self, file_name, depth = -1, source = None):
        self._file_name = file_name
        self._depth = depth
        self._source = source

    def set_depth(self, depth):
        self._depth = depth

    def set_source(self, source):
        self._source = source

    def get_file_name(self):
        return self._file_name

    def get_source(self):
        return self._source
    
    def get_depth(self):
        return self.depth

def parse_options():
    """options for move file helper
    """
    option_parser = OptionParser(usage = "\
            %prog [options] filename")
    setup_options(option_parser)

    option_parser.add_option('-f', '--filename', dest = 'filename', \
            type = 'string', help = "filename to move")
    option_parser.add_option('-d', '--depth', dest = 'depth', \
            type = 'int', help ='output depth')
    option_parser.add_option('-a', '--all', action = 'store_true', \
            dest = 'print_all', help = \
            'print all files that involved in the file you want move')

    return option_parser.parse_args()

def file_handler(file_name, get_tu_func, \
        depth, base_lib_name, output_list):

    if depth < 1:
        return
    depth -= 1

    source_tu = get_tu_func(file_name)
    if not source_tu:
        raise ValueError, "Can't get tu for %s " % file_name

    for include in source_tu.get_includes():
        if include.depth == 1 and \
                get_lib_name(include.include.name) == base_lib_name:
            source_file_name = get_source_file(include.include.name)
            if source_file_name:
                includeObj = IncludeObject(source_file_name)
                includeObj.set_depth(depth)
                includeObj.set_source(file_name)
                output_list.append(includeObj)
                file_handler(source_file_name, \
                        get_tu_func, depth, base_lib_name, output_list)

def get_source_file(fpath):
    """from header file path to get source file path
    """
    for file_name in get_source_path_candidates(fpath):
        if os.path.isfile(file_name):
            return os.path.abspath(file_name)

def main():
    """main function
    """
    options, args = parse_options()
    if not options.filename:
        print 'Error : no input file'
        sys.exit(-1)

    if not os.path.isfile(options.filename):
        print 'Error : %s no such file' % options.filename
        sys.exit(-1)

    file_name = os.path.abspath(options.filename)
    lib_name = get_lib_name(file_name)

    output_list = []
    file_handler(file_name, partial(get_tu, cdb_path = options.cdb_path, config_path = options.config), \
            options.depth, lib_name, output_list)
    pdb.set_trace()

if __name__ == '__main__':
    main()

