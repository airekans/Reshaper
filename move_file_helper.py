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

def get_source_file(fpath):
    '''from header file path to get source file path
    '''
    for file_name in get_source_path_candidates(fpath):
        if os.path.isfile(file_name):
            return os.path.abspath(file_name)


class IncludeObject(object):
    '''class to cache include information
    '''
    def __init__(self, file_name = "", depth = -1, source = ""):
        self.file_name = file_name
        self.depth = depth
        self.source = source
        self.can_be_moved = False

    def set_can_be_moved(self, can_be_moved = True):
        '''if this file_name can be moved
        '''
        self.can_be_moved = can_be_moved

class MoveFileHandle(object):
    '''used to pass file get move helper information
    '''
    def __init__(self, get_tu_func, file_name = "", \
            lib_name = "", depth = 1):
        self._lib_name = lib_name
        self._file_name = get_source_file(file_name)
        self._get_tu_func = get_tu_func
        self._max_depth = depth
        self._already_handle_list = []
        self._output_list = []

    def get_includes_for_source_file(self, header_name, \
            source_file, source_includes):
        '''get includes list for source file
        '''
        includes = []
        source_tu = self._get_tu_func(source_file)
        if not source_tu:
            return includes

        # update includes
        source_includes = source_tu.get_includes()

        for include in source_tu.get_includes():
            if os.path.abspath(include.include.name) == header_name:
                continue
            if include.depth == 1 and \
                get_lib_name(include.include.name) == self._lib_name:
                includes.append(include.include.name)
        return includes

    def get_includes_for_header_file(self, header_name, source_includes):
        '''get includes list for header file,
        we have to use tu.get_includes() of its source file
        '''
        include_list = []
        if not source_includes:
            return include_list

        depth = -1
        header_name = os.path.abspath(header_name)

        for include in source_includes:
            if depth == -1:
                if os.path.abspath(include.include.name) == header_name:
                    depth = include.depth
            else:
                assert(depth >=0)
                if include.depth == depth + 1 and \
                    get_lib_name(include.include.name) == self._lib_name:
                    include_list.append(include.include.name)
                if include.depth >= depth:
                    break

        return include_list

    def _get_include_recurvely(self, header_name,
            current_depth, source_includes):
        '''get include file recurvely
        '''
        include_obj = IncludeObject(header_name, current_depth)

        should_return = False
        if current_depth >= self._max_depth:
            should_return = True
        if header_name in self._already_handle_list:
            should_return = True

        current_depth += 1
        self._already_handle_list.append(header_name)

        file_includes = []
        source_file = get_source_file(header_name)

        if source_file and source_file in self._already_handle_list:
            return

        if not source_file:
            file_includes = self.get_includes_for_header_file(header_name, \
                    source_includes)
        else:
            file_includes = self.get_includes_for_source_file(header_name, \
                    source_file, source_includes)
     
        if not file_includes:
            include_obj.set_can_be_moved(True)
        self._output_list.append(include_obj)

        if should_return:
            return

        for file_obj in file_includes:
            self._get_include_recurvely(file_obj, \
                    current_depth, source_includes)

    def begin_to_handle(self):
        '''entrance to handle a file
        '''
        if self._max_depth < 1:
            return

        self._already_handle_list.append(self._file_name)
        try:
            source_tu = self._get_tu_func(self._file_name)
        except Exception:
            raise ValueError, "Can't get tu for %s " % self._file_name

        includes = []
        for include in source_tu.get_includes():
            if include.depth == 1 and \
                    get_lib_name(include.include.name) == self._lib_name:
                includes.append(include.include.name)
        for file_obj in includes:
            self._get_include_recurvely(file_obj, 1, source_tu.get_includes())

    def begin_to_handle_for_UT(self, source_tu):
        '''this is used for unittest
        '''
        includes = []
        for include in source_tu.get_includes():
            if include.depth == 1 and \
                    get_lib_name(include.include.name) == self._lib_name:
                includes.append(include.include.name)
        for file_obj in includes:
            self._get_include_recurvely(file_obj, 1, source_tu.get_includes())

    def get_output_list(self):
        '''return output list of IncludeObject
        '''
        if not self._output_list:
            self.begin_to_handle()
        return self._output_list


def parse_options():
    """options for move file helper
    """
    option_parser = OptionParser(usage = "\
            %prog [options] filename")
    setup_options(option_parser)

    option_parser.add_option('-d', '--depth', dest = 'depth', default = 1, \
            type = 'int', help ='depth to generator, default is 1.')
    return option_parser.parse_args()

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
        if not lib_name:
            print "Error : Can't get lib name, %s" % file_path
            continue

        file_handler = MoveFileHandle(\
                partial(get_tu, cdb_path = options.cdb_path, \
                    config_path = options.config), 
                file_name, lib_name, options.depth)

        print "-------------------------------------------------"
        print file_name
        for obj in file_handler.get_output_list():
            out_str = obj.depth * "**" + " "  + os.path.abspath(obj.file_name)
            print out_str + "*" if obj.can_be_moved else out_str

if __name__ == '__main__':
    main()

