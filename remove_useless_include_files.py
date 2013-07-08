#!/usr/bin/env python

import os, sys, re
from optparse import OptionParser
from functools import partial
from clang.cindex import TranslationUnit
from reshaper.ast import get_tu
from reshaper.util import walk_ast, get_declaration
from reshaper.semantic import scan_dir_parse_files

def parse_options():
    option_parser = OptionParser(usage = "\
            %prog [options] FILENAME")

    option_parser.add_option("-f", "--filename", dest = "filename", \
            type = "string", help = "filename to get useless include list")
    option_parser.add_option("-c", "--cdb_path", dest = "cdb_path", \
            type = "string", help = "cdb path")
    option_parser.add_option("-d", "--directory", dest = "directory", \
            type = "string", help = "directory to get useless include list")

    return option_parser.parse_args()

def compare_file_name(cursor, level, base_filename):
    if cursor.location.file is not None:
       cursor_filename = cursor.location.file.name

       basename_withoutext_file = os.path.splitext(os.path.basename(base_filename))[0]
       basename_withoutext_cursor = os.path.splitext(os.path.basename(cursor_filename))[0]
       return basename_withoutext_file == basename_withoutext_cursor
    return True

def get_lib_name(filename):
    abs_file_name = os.path.abspath(filename)
    if "SQL" in abs_file_name:
        return "SQL"

    if "/lib" in abs_file_name:
        return 
    
    dir_name = os.path.dirname(abs_file_name)
    if dir_name is None:
        return None

    if os.path.basename(dir_name) == "src":
        dir_name = os.path.dirname(dir_name)

    split_text = dir_name.split("/lib")


def get_useful_header_file(cursor, level, header_list):
    if cursor is None:
        return
    decla_cursor = get_declaration(cursor)
    if decla_cursor is None or decla_cursor.location is None or decla_cursor.location.file is None:
        return

    include_name = decla_cursor.location.file.name
    if include_name not in header_list:
        header_list.append(os.path.abspath(include_name))

def handler_file(filename, cdb_path):
    useless_list = get_useless_include_list(filename, cdb_path)
    remove_useless_list(filename, useless_list)

def get_useless_include_list(filename, cdb_path):
    file_name = os.path.abspath(filename)

    if cdb_path is None:
        source_tu = get_tu(file_name, options=1)
    else:
        source_tu = get_tu(file_name, cdb_path=cdb_path, options=1)

    if source_tu is None:
        print "Failed to get TranslationUnit for %s." % file_name
        return

    useful_include_list= []
    walk_ast(source_tu,\
            partial(get_useful_header_file, header_list = useful_include_list),\
            partial(compare_file_name, base_filename = file_name))

    header_list = []
    for include_file in source_tu.get_includes():
        if include_file.depth == 1:
            header_list.append(os.path.abspath(str(include_file.include)))

    useless_include_list = []
#    print "%s---------suggest to remove header file list--------" % file_name
    for file in header_list:
        if file not in useful_include_list and\
                not os.path.basename(file) == "precompile.h":
             useless_include_list.append(file)
             #print file

    return useless_include_list

def remove_useless_list(filename, include_list):
    #checkout
    os.system("p4 edit %s" % filename)

    file_name = os.path.abspath(filename)
    match_list = []
    file_obj = open(file_name, 'r+')
    tmp_file_name = "%s.bak.tmp" % file_name
    write_obj = open(tmp_file_name, 'w')

    for file in include_list:
        basename = os.path.basename(file)
        pattern = re.compile('^(#include).*(%s").*' % basename)
        match_list.append(pattern)

    line_no = 0
    max_include_lines = 100
    while 1:
        line = file_obj.readline()
        if not line:
            break

        line_no += 1
        match_pattern = False
        if line and line_no < max_include_lines:
            for pattern in match_list:
                if pattern.search(line):
                    match_pattern = True
                    print line
                    break

        if not match_pattern:
            write_line = "%s" % line
            write_obj.write(write_line)

    os.remove(file_name)
    os.rename(tmp_file_name, file_name)

def main():
    options, args = parse_options()

    if options.filename is None and options.directory is None:
        print "please input filename or directory."
        sys.exit(-1)

    if options.filename is not None and \
            not os.path.isfile(options.filename):
        print "%s : no such file." % options.filename
        sys.exit(-1)

    if options.directory is not None and \
            os.path.isdir(options.directory):
        print "%s : no such directory." % options.directory
        sys.exit(-1)

    if options.filename:
        handler_file(options.filename, options.cdb_path)

    if options.directory:
        scan_dir_parse_files(options.directory,\
                partial(handler_file, cdb_path = options.cdb_path))


if __name__ == "__main__":
    main()

