#!/usr/bin/env python

"""remove_useless_include_files.py 
tools used to remove useless include files,
should make sure that the length of include files 
cannot be over 100 lines
"""
import os, sys, re
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

def get_useful_include_file(cursor, level, header_list):
    """walk ast to get useful header files
    """
    if cursor is None:
        return
    decla_cursor = get_declaration(cursor)
    if decla_cursor is None or decla_cursor.location is None or \
            decla_cursor.location.file is None:
        return

    include_name = decla_cursor.location.file.name
    if include_name not in header_list:
        header_list.append(os.path.abspath(include_name))

def handle_file(filename, cdb_path, config_path, remove_origin_file):
    """handler filename to remove useless include files
    """
    file_name = os.path.abspath(filename)
    useless_list = get_useless_include_list(file_name, cdb_path, config_path)
    tmpfile = remove_useless_includes(file_name, useless_list)
    if remove_origin_file and tmpfile:
        replace_files_and_checkout(file_name, tmpfile)

def replace_files_and_checkout(filename, newname):
    """checkout, remove and rename
    """
    if os.system("p4 edit %s" % filename):
        sys.exit(-1)
    if os.remove(filename):
        print "remove %s error!" % filename
        sys.exit(-1)
    if os.rename(newname, filename):
        print "rename %s to %s error!" % (newname, filename)
        sys.exit(-1)

def get_useless_include_list(filename, cdb_path, config_path):
    """get useless include list for filename
    """
    if cdb_path is None:
        source_tu = get_tu(filename, options=1)
    else:
        source_tu = get_tu(filename, cdb_path=cdb_path, \
                config_path = config_path, options=1)

    if source_tu is None:
        print "Failed to get TranslationUnit for %s." % filename
        return

    useful_include_list = []
    walk_ast(source_tu, \
            partial(get_useful_include_file, header_list = useful_include_list), \
            partial(compare_file_name, base_filename = filename))

    header_list = []
    for include_file in source_tu.get_includes():
        if include_file.depth == 1:
            header_list.append(os.path.abspath(str(include_file.include)))

    useless_include_list = []
    for f in header_list:
        if f not in useful_include_list and\
                not os.path.basename(f) == "precompile.h":
            useless_include_list.append(f)

    return useless_include_list

def remove_useless_includes(filename, include_list):
    """remove useless include files in filename and 
    output result to filename.header.bak
    """
    if not include_list:
        return None

    tmp_file_name = "%s.header.bak" % filename
    # gen match_pattern list
    match_list = []
    for f in include_list:
        basename = os.path.basename(f)
        pattern = re.compile('^(#include).*(%s").*' % basename)
        match_list.append(pattern)

    # file handle : remove useless include files
    try:
        file_obj = open(filename, 'r')
        write_obj = open(tmp_file_name, 'w')

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
                        break

            if not match_pattern:
                write_line = "%s" % line
                write_obj.write(write_line)

        file_obj.close()
        write_obj.close()
    except IOError, err:
        print err
        sys.exit(-1)

    return tmp_file_name

def main():
    """main function
    """
    options, args = parse_options()

    if options.filename is None and options.directory is None:
        print "please input filename or directory."
        sys.exit(-1)

    if options.filename is not None and \
            not os.path.isfile(options.filename):
        print "%s : no such file." % options.filename
        sys.exit(-1)

    if options.directory is not None and \
            not os.path.isdir(options.directory):
        print "%s : no such directory." % options.directory
        sys.exit(-1)

    if options.filename:
        handle_file(options.filename, options.cdb_path, \
                options.config, options.remove)

    if options.directory:
        scan_dir_parse_files(options.directory, \
                partial(handle_file, cdb_path = options.cdb_path, \
                config_path = options.config, remove_origin_file = options.remove))

if __name__ == "__main__":
    main()

