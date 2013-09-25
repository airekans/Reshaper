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
from reshaper.semantic import is_header, get_lib_name, get_source_path_candidates

def get_source_file(fpath):
    '''from header file path to get source file path
    '''
    for file_name in get_source_path_candidates(fpath):
        if os.path.isfile(file_name):
            return os.path.abspath(file_name)
    return None

def get_header_file_name(fpath):
    '''get file name without extend
    '''
    if is_header(fpath):
        return fpath
    if not os.path.isfile(fpath):
        return ''
    dir_name, base_name = os.path.split(fpath)
    fname, _ = os.path.splitext(base_name)

    sub_dir_candidates = ['', '..']
    surfix_candidates = ['.h', '.hh', '.hpp']

    for file_name in [os.path.join(dir_name, sub_dir, fname + surfix) \
            for sub_dir in sub_dir_candidates \
            for surfix in surfix_candidates]:
        if os.path.isfile(file_name):
            return os.path.abspath(file_name)

class IncludeInfo(object):
    '''class to cache include information
    '''
    def __init__(self, file_name = "", depth = -1, source = ""):
        self.file_name = file_name
        self.depth = depth
        self.source = source
        self.can_be_moved = False
        self.have_parsed = False

    def set_can_be_moved(self, can_be_moved = True):
        '''if this file_name can be moved
        '''
        self.can_be_moved = can_be_moved

    def set_have_been_parsed(self, parsed = True):
        '''if this file is parsed already
        '''
        self.have_parsed = parsed

class MoveFileHandler(object):
    '''used to pass file get move helper information
    '''
    def __init__(self, get_tu_func, file_name = "", \
            lib_name = "", depth = 1):
        self._lib_name = lib_name
        self._file_name = get_source_file(file_name)
        self._get_tu_func = get_tu_func
        self._max_depth = depth
        self._already_handle_list = set()
        self._output_list = []
        self._includes_cache = {}
        self._no_hint = False

    def set_no_hint(self, no_hint = True):
        '''no need to hint
        '''
        self._no_hint = no_hint

    def get_includes_for_source_file(self, header_name, \
            source_file):
        '''get includes list for source file
        '''
        return self._get_includes(source_file, header_name)

    def get_includes_for_header_file(self, header_name, source_includes):
        '''get includes list for header file,
        we have to use tu.get_includes() of its source file
        '''
        include_list = []
        if not source_includes:
            return include_list

        for include in source_includes:
            if os.path.abspath(include.source.name) == header_name and \
                get_lib_name(include.include.name) == self._lib_name:
                include_list.append(include.include.name)

        return include_list

    def _get_include_recursively(self, header_name,
            current_depth, source_includes):
        '''get include file recurvely
        '''
        header_name = os.path.abspath(header_name)
        include_obj = IncludeInfo(header_name, current_depth)

        # if it reaches max depth, set should_return to True 
        should_return = False
        if current_depth >= self._max_depth:
            should_return = True
        
        # if need hint (self._no_hint is False), not return directly,
        # go on to parse this file to get hint info (can_be_moved)
        if should_return and self._no_hint:
            return

        if header_name in self._already_handle_list:
            include_obj.set_have_been_parsed()
            self._output_list.append(include_obj)
            return

        if not should_return:
            current_depth += 1
            self._already_handle_list.add(header_name)

        file_includes = []
        source_file = get_source_file(header_name)

        if source_file and source_file in self._already_handle_list:
            return

        if not source_file:
            file_includes = self.get_includes_for_header_file(header_name, \
                    source_includes)
        else:
            file_includes, source_includes = \
                    self.get_includes_for_source_file(\
                    header_name, source_file)
     
        if not file_includes:
            include_obj.set_can_be_moved(True)

        self._output_list.append(include_obj)

        if should_return:
            return

        for file_obj in file_includes:
            self._get_include_recursively(file_obj, \
                    current_depth, source_includes)

    def begin_to_handle(self):
        '''entrance to handle a file
        '''
        if self._max_depth < 1:
            return

        header_name = get_header_file_name(self._file_name)
        self._already_handle_list.add(header_name)
        self._output_list.append(IncludeInfo(header_name, 1))

        includes, source_includes  = \
                self._get_includes(self._file_name, header_name)

        for file_obj in includes:
            self._get_include_recursively(file_obj, 1, source_includes)

    def _get_includes(self, file_name, header_name = ''):
        ''' get includes under self.lib_name for a file
        1) file_name
        2) source_includes is return value
        3) header file name
        '''
        includes = []
        try:
            source_tu = self._get_tu_func(file_name)
        except Exception:
            raise ValueError, "Can't get tu for %s" % file_name


        # get includes in source file
        for include in source_tu.get_includes():
            if os.path.abspath(include.include.name) == header_name:
                continue
            if include.depth == 1 and \
                    get_lib_name(include.include.name) == self._lib_name:
                includes.append(include.include.name)
        # get includes in header file
        if header_name:
            includes.extend(self.get_includes_for_header_file(header_name, \
                    source_tu.get_includes()))

        # add source_tu to cache, or else source_tu.get_includes() iterator will
        # be deleted.
        self._includes_cache[file_name] = source_tu
        return includes, source_tu.get_includes()

    def get_output_list(self):
        '''return output list of IncludeInfo
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
    option_parser.add_option('-n', '--no-hint', \
            action = 'store_true', dest = 'no_hint', \
            help = "don't 'need hint to suggest if leaf" 
            ' node file can be moved or not'
            )
    return option_parser.parse_args()

def main():
    """main function
    """
    options, args = parse_options()

    if len(args) < 1:
        sys.stderr.write('Error : Please input file to parse')
        sys.exit(-1)

    for file_path in args:
        file_name = os.path.abspath(file_path)
        if not os.path.isfile(file_name):
            sys.stderr.write('Error : No such file, %s' % file_path)
            continue
        lib_name = get_lib_name(file_name)
        if not lib_name:
            sys.stderr.write("Error : Can't get lib name, %s" % file_path)
            continue

        file_handler = MoveFileHandler(\
                partial(get_tu, cdb_path = options.cdb_path, \
                    config_path = options.config), 
                file_name, lib_name, options.depth)
        if options.no_hint:
            file_handler.set_no_hint()

        print "-------------------------------------------------"
        print file_name
        for obj in file_handler.get_output_list():
            out_str = obj.depth * "**" + " "  + os.path.abspath(obj.file_name)
            if not options.no_hint:
                out_str += "*" if obj.can_be_moved else ''
                out_str += " ~" if obj.have_parsed else ''
            print out_str

if __name__ == '__main__':
    main()

