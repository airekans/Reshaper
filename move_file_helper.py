#!/usr/bin/env python

"""move files helper
this script is used to move files;
if you want to move file A.cpp under libB,
it can find out all files that used(directly or indirectly)
by A.cpp under libB
"""
import os, sys
from optparse import OptionParser
from functools import partial
from reshaper.option import setup_options
from reshaper.ast import get_tu
from reshaper.semantic import get_lib_name, get_source_path_candidates

_global_include_list = []
class IncludeObject(object):
    """class to cache include information
    """
    def __init__(self, file_name, depth = -1, source = None):
        self._file_name = file_name
        self._depth = depth
        self._source = source
        self._parent_chain = ""

    def set_depth(self, depth):
        """depth of this include file
        """
        self._depth = depth

    def set_source(self, source):
        """its source file, who include it
        """
        self._source = source

    def get_file_name(self):
        """file name of this object
        """
        return self._file_name

    def get_source(self):
        """get source file name who include it
        """
        return self._source
    
    def get_depth(self):
        """get depth
        """
        return self._depth

def parse_options():
    """options for move file helper
    """
    option_parser = OptionParser(usage = "\
            %prog [options] filename")
    setup_options(option_parser)

    option_parser.add_option('-d', '--depth', dest = 'depth', default = 1, \
            type = 'int', help ='depth to generator, default is 1.')
    return option_parser.parse_args()

def get_includes_with_lib(file_name, header_name, get_tu_func, \
        depth, base_lib_name, output_list):
    """get include files who's in the same lib as base_lib_name
       file_name : source file name
       get_tu_func : function to get TranslationUnit
       depth : file depth
       base_lib_name : lib name
       output_list : output include information list
    """
    if file_name in _global_include_list :
        return

    if depth < 1:
        return
    depth -= 1

    _global_include_list.append(file_name)
    source_tu = get_tu_func(file_name)

    if not source_tu:
        raise ValueError, "Can't get tu for %s " % file_name

    for include in source_tu.get_includes():
        if include.depth == 1 and \
                get_lib_name(include.include.name) == base_lib_name:

            include_obj = IncludeObject(include.include.name)
            include_obj.set_depth(depth)
            include_obj.set_source(file_name)
            if not header_name == include.include.name:
                output_list.append(include_obj)

            source_file_name = get_source_file(include.include.name)

            if source_file_name: #and source_file_name != file_name:
                get_includes_with_lib(source_file_name, include.include.name,\
                        get_tu_func, depth, base_lib_name, output_list)

def get_source_file(fpath):
    """from header file path to get source file path
    """
    for file_name in get_source_path_candidates(fpath):
        if os.path.isfile(file_name):
            return os.path.abspath(file_name)

def get_all_related_cpp(fpath, base_lib_name, get_tu_func):
    source_tu = get_tu_func(fpath)
    include_dict = {}
    for include in source_tu.get_includes():
        if get_lib_name(include.include.name) == base_lib_name:
            source_file_name = get_source_file(include.include.name)
            if source_file_name:
                include_dict[source_file_name] = include.source
    return include_dict

def main():
    """main function
    """
    options, args = parse_options()

    if len(args) < 1:
        print 'Error : Please input file to parse'
        sys.exit(-1)

    for file_path in args:
        file_name = os.path.abspath(file_path)
        if not os.path.isfile(file_name):
            print 'Error : No such file, %s' % file_path
            continue
        lib_name = get_lib_name(file_name)

        output_list = []
        get_includes_with_lib(file_name, '',\
            partial(get_tu, cdb_path = options.cdb_path, \
                config_path = options.config), \
            options.depth, lib_name, output_list)

        include_dict = get_all_related_cpp(file_name, lib_name,\
                partial(get_tu, cdb_path = options.cdb_path,\
                config_path = options.config))

        for key in include_dict.keys():
            if key not in _global_include_list:
                print key

        print "-------------------------------------------------"
        print file_name
        for obj in output_list:
            print (options.depth - obj.get_depth()) * "**", \
                    os.path.abspath(obj.get_file_name())

if __name__ == '__main__':
    main()

