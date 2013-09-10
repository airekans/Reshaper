#!/usr/bin/env python

"""remove_invalid_includes.py 
tools used to remove invalid include files,
"""
import os, sys, re
from clang.cindex import TranslationUnit, TypeKind
from optparse import OptionParser
from functools import partial
from reshaper.option import setup_options
from reshaper.ast import get_tu
from reshaper.util import walk_ast, get_declaration
from reshaper.semantic import walkdir
from reshaper.find_reference_util import compare_file_name

def parse_options():
    """options for remove invalid include files
    """
    option_parser = OptionParser(usage = "\
            %prog [options] FILENAME or DERECTORY")

    setup_options(option_parser)
    option_parser.add_option("-f", "--filename", dest = "filename", \
            type = "string", help = "filename to get invalid include list")
    option_parser.add_option("-d", "--directory", dest = "directory", \
            type = "string", help = "directory to get invalid include list")
    option_parser.add_option("-i", "--in-place", action = "store_true", \
            dest = "inplace", help = \
            "if given, will checkout files and remove invalid include files."
            "or else, will generator new files postfix with .header.bak.")

    return option_parser.parse_args()

def add_cursor_file(cursor, level, header_list):
    """visitor for walk ast to get useful header files
    """
    if cursor is None:
        return
    decl_cursor = get_declaration(cursor)
    if decl_cursor is None or decl_cursor.location is None or \
            decl_cursor.location.file is None:
        return

    include_name = os.path.abspath(decl_cursor.location.file.name)
    if include_name not in header_list:
        header_list.append(include_name)

    if decl_cursor.type.kind == TypeKind.FUNCTIONPROTO:
        for child in decl_cursor.get_children():
            add_cursor_file(child, level, header_list = header_list)

class IncludeHandler(object):
    """class to handle include files,
    purpose if to remove invalid include files
    """
    def __init__(self, filename, cdb_path = None, \
            config_path = "~/.reshaper.cfg", \
            options = TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD):
        self._file_name = os.path.abspath(filename)
        if not os.path.isfile(self._file_name):
            raise ValueError, "%s : No such file!"

        self._tu = get_tu(self._file_name, cdb_path = cdb_path, \
                config_path = config_path, options = options)

        if not self._tu:
            raise ValueError, "Can't get TranslationUnit for %s" \
                    % self._file_name

        self._useful_list = []
        self._invalid_list = []
        self._indirect_dict = {}
        self._header_list = []
        self._temp_file = None

    def get_useful_includes(self):
        """ return include files that indeed used.
        To be careful : itself will also in useful includes
            and no need to filter it.
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

    def get_invalid_includes(self):
        """get invalid include files
        """
        if self._invalid_list:
            return self._invalid_list

        if not self._header_list:
            self.get_header_list()
        if not self._useful_list:
            self.get_useful_includes()
        if not self._indirect_dict:
            self._gen_indirect_includes()

        # get not direct include files
        tmp_list = [item for item in self._header_list \
                if item not in self._useful_list]

        # if a.cpp -> b.h -> c.h and c.h is indeed used by a.cpp,
        # we can't remove b.h
        inter_list = [item for item in self._useful_list \
                if item in self._indirect_dict]
        indirect_list = set()
        for c in inter_list:
            f = self._indirect_dict[c]
            indirect_list.add(f)

        self._invalid_list = filter(lambda x : x not in indirect_list, tmp_list)

        return self._invalid_list

    def get_header_list(self):
        """ get directly include files;
        FIXME: if a.h and b.h is included, and a.h is also included by b.h
        the depth of a.h depends on a.h and b.h which is include first.
        1) if include a.h first, it's depth is 1, 
        2) if include b.h first, it's depth is 2
        """
        if not self._header_list:
            for include_file in self._tu.get_includes():
                if include_file.depth == 1:
                    self._header_list.append( \
                            os.path.abspath(include_file.include.name))
        return self._header_list

    def gen_clean_include_file(self, postfix = ".header.bak"):
        """remove invalid include files in filename 
        and generator temp file with postfix
        """
        if not self._invalid_list:
            self.get_invalid_includes()

        if not self._invalid_list:
            return

        # get tmp_file_name
        tmp_file_name = "%s%s" % (self._file_name, postfix)
        # gen pattern to get includes
        pattern = re.compile(r'^(#include) *[<"](?P<include_str>.*)[>"]')
        # handle file
        '''
        open file to get contents and write to new file according to:
        1) use pattern.search to get all includes
        2) if search succeed, include filename will be the 2nd element of
            the group,(between " and ")
        3) search invalid includes list, if it not in invalid list, write it
            to new tmp_file
        '''
        try:
            file_obj = open(self._file_name, 'r')
            write_obj = open(tmp_file_name, 'w')

            for line in file_obj:
                match_pattern = False
                ret_search = pattern.search(line)
                if ret_search :
                    include_str = ret_search.group('include_str')
                    for f in self._invalid_list:
                        if include_str in f:
                            match_pattern = True
                            break

                if not match_pattern:
                    write_obj.write(line)

            self._temp_file = tmp_file_name
        except IOError, err:
            print err
            sys.exit(-1)
        finally:
            file_obj.close()
            write_obj.close()

    def get_clean_include_file(self):
        """get clean include file
        """
        if not self._temp_file:
            self.gen_clean_include_file()

        return self._temp_file

    def remove_invalid_includes(self):
        """remove invalid includes for source file
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

def get_used_include_file(filename, \
        cdb_path, config_path, remove_origin_file):
    """ handle file to remove invalid include files
    """
    file_obj = IncludeHandler(filename, cdb_path = cdb_path, \
            config_path = config_path)
    tmp_file = file_obj.get_clean_include_file()
    if not tmp_file:
        print 'Info: %s has no invalid includes' % filename
        return

    if remove_origin_file:
        file_obj.checkout()
        file_obj.remove_invalid_includes()
    else:
        print 'Info: %s finished, result file is %s' % \
                (filename, tmp_file)

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
        get_used_include_file(options.filename, options.cdb_path, \
                options.config, options.inplace)
    elif options.directory:
        walkdir(options.directory, \
                partial(get_used_include_file, \
                    cdb_path = options.cdb_path, \
                    config_path = options.config, \
                    remove_origin_file = options.inplace))

if __name__ == "__main__":
    main()

