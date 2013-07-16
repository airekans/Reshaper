#!/usr/bin/env python

"""remove_useless_include_files.py 
tools used to remove useless include files,
should make sure that the length of include files 
cannot be over 100 lines
"""
import os, sys, re
from clang.cindex import TypeKind
from optparse import OptionParser
from functools import partial
from reshaper.option import setup_options
from reshaper.ast import get_tu
from reshaper.util import walk_ast, get_declaration
from reshaper.semantic import scan_dir_parse_files
from reshaper.find_reference_util import compare_file_name

def parse_options():
    """options for remove useless include files
    """
    option_parser = OptionParser(usage = "\
            %prog [options] FILENAME or DERECTORY")

    setup_options(option_parser)
    option_parser.add_option("-f", "--filename", dest = "filename", \
            type = "string", help = "filename to get useless include list")
    option_parser.add_option("-d", "--directory", dest = "directory", \
            type = "string", help = "directory to get useless include list")
    option_parser.add_option("-r", "--remove", action = "store_true", \
            dest = "remove", help = \
            "if given, will checkout files and remove useless include files."
            "or else, will generator new files postfix with .header.bak.")

    return option_parser.parse_args()

def add_cursor_file(cursor, level, header_list):
    """visitor for walk ast to get useful header files
    """
    if cursor is None:
        return
    decla_cursor = get_declaration(cursor)
    if decla_cursor is None or decla_cursor.location is None or \
            decla_cursor.location.file is None:
        return

    include_name = os.path.abspath(decla_cursor.location.file.name)
    if include_name not in header_list:
        header_list.append(include_name)

    if decla_cursor.type.kind == TypeKind.FUNCTIONPROTO:
        for child in decla_cursor.get_children():
            add_cursor_file(child, level, header_list = header_list)

class IncludeHandler(object):
    """class to handle include files,
    purpose if to remove useless include files
    """
    def __init__(self, filename, cdb_path = None, \
            config_path = "~/.reshaper.cfg", options = 1):
        """should make sure that filename is exists
        """
        self._file_name = os.path.abspath(filename)
        if not os.path.isfile(self._file_name):
            raise ValueError, "%s : No such file!"

        if cdb_path is None:
            self._tu = get_tu(self._file_name, \
                    config_path = config_path, options = options)
        else:
            self._tu = get_tu(self._file_name, cdb_path = cdb_path, \
                    config_path = config_path, options = options)

        if not self._tu:
            raise ValueError, "Can't get TranslationUnit for %s" \
                    % self._file_name

        self._useful_list = []
        self._useless_list = []
        self._indirect_dict = {}
        self._header_list = []
        self._temp_file = None

    def get_useful_includes(self):
        """ return include files that indeed used 
        """
        if not self._useful_list:
            walk_ast(self._tu, \
                    partial(add_cursor_file, header_list = self._useful_list),
                    partial(compare_file_name, base_filename = self._file_name))
        return self._useful_list

    def _gen_indirect_includes(self):
        """ return include files that,
        should make sure that return values of 
        """
        if self._indirect_dict:
            return self._indirect_dict

        direct_include = None
        for include in self._tu.get_includes():
            if include.depth == 1:
                direct_include = os.path.abspath(include.include.name)
            if not include.depth == 1:
                self._indirect_dict[os.path.abspath(include.include.name)] \
                       = direct_include

    def get_useless_includes(self):
        """get useless include files
        """
        if self._useless_list:
            return self._useless_list

        if not self._header_list:
            self.get_header_list()
        if not self._useful_list:
            self.get_useful_includes()
        if not self._indirect_dict:
            self._gen_indirect_includes()

        # get not direct include files
        tmp_list = [item for item in self._header_list \
                if item not in self._useful_list]

        inter_list = [item for item in self._useful_list \
                if item in self._indirect_dict.keys()]

        indirect_list = []
        for c in inter_list:
            f = self._indirect_dict[c]
            if f not in indirect_list:
                indirect_list.append(f)

        self._useless_list = filter(lambda x : x not in indirect_list, tmp_list)

        return self._useless_list

    def get_header_list(self):
        """ get directly include files
        """
        if not self._header_list:
            for include_file in self._tu.get_includes():
                if include_file.depth == 1:
                    self._header_list.append( \
                            os.path.abspath(include_file.include.name))
        return self._header_list

    def gen_clean_include_file(self, postfix = ".header.bak"):
        """remove useless include files in filename 
        and generator temp file with postfix
        """
        if not self._useless_list:
            self.get_useless_includes()

        if not self._useless_list:
            return

        # get tmp_file_name
        tmp_file_name = "%s%s" % (self._file_name, postfix)
        # gen pattern to get includes
        pattern = re.compile('^(#include) *[<"](.*)[>"]')
        # handle file
        try:
            file_obj = open(self._file_name, 'r')
            write_obj = open(tmp_file_name, 'w')

            line_no = 0
            max_include_lines = 250
            while 1:
                line = file_obj.readline()
                if not line:
                    break

                line_no += 1
                match_pattern = False
                if line and line_no < max_include_lines:
                    ret_search = pattern.search(line)
                    if ret_search and len(ret_search.groups()) > 1:
                        include_str = ret_search.group(2)
                        for f in self._useless_list:
                            if include_str in f:
                                match_pattern = True
                                break

                if not match_pattern:
                    write_obj.write(line)

            file_obj.close()
            write_obj.close()
            self._temp_file = tmp_file_name
        except IOError, err:
            print err
            sys.exit(-1)

        return self._temp_file

    def get_clean_include_file(self):
        """get clean include file
        """
        if not self._temp_file:
            self.gen_clean_include_file()

        return self._temp_file

    def remove_useless_includes(self):
        """remove useless includes for source file
        """
        if not self._temp_file:
            self.gen_clean_include_file()
        if os.remove(self._file_name):
            print "remove %s error!" % self._file_name
            sys.exit(-1)

        if os.rename(self._temp_file, self._file_name):
            print "rename %s to %s error!" % (self._temp_file, self._file_name)
            sys.exit(-1)

    def checkout(self, cmd = "p4 edit"):
        """checkout in p4
        """
        if os.system("%s %s" % (cmd, self._file_name)):
            print "checkout %s error!" % self._file_name
            sys.exit(-1)

def handle_file(filename, cdb_path, config_path, remove_origin_file):
    """ handle file to remove useless include files
    """
    file_obj = IncludeHandler(filename, cdb_path = cdb_path, \
            config_path = config_path)
    tmp_file = file_obj.get_clean_include_file()

    if remove_origin_file:
        tmp_file.checkout()
        tmp_file.remove_useless_includes()

def main():
    """main function
    """
    options, args = parse_options()

    if not options.filename and not options.directory:
        print "Error : please input filename or directory."
        sys.exit(-1)

    if options.filename is not None and \
            not os.path.isfile(options.filename):
        print "Error : %s, no such file." % options.filename
        sys.exit(-1)

    if options.directory is not None and \
            not os.path.isdir(options.directory):
        print "Error : %s, no such directory." % options.directory
        sys.exit(-1)

    if options.filename:
        handle_file(options.filename, options.cdb_path, \
                options.config, options.remove)

    if options.directory:
        scan_dir_parse_files(options.directory, \
                partial(handle_file, cdb_path = options.cdb_path, \
                config_path = options.config, \
                remove_origin_file = options.remove))

if __name__ == "__main__":
    main()

