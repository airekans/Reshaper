#!/usr/bin/env python

"""update_indexer.py -- used to update indexer for specific file or directory
"""

import os, sys
import bsddb
from optparse import OptionParser
from functools import partial
from clang.cindex import TranslationUnit, Cursor, CursorKind
from reshaper.util import get_tu, walk_ast
from reshaper.semantic import check_diagnostics
from reshaper.semantic import scan_dir_parse_files
from reshaper.find_reference_util import get_usr_of_declaration_cursor

def parse_options():
    """ parse input options for update_indexer
    """

    option_parser = OptionParser(usage = "\
            %prog [options] FILENAME or DIRECTORY")
    option_parser.add_option("-f", "--file", dest = "filename", \
            type = "string", help = "file to update")
    option_parser.add_option("-d", "--directory", dest = "directory",\
            type = "string", help = "directory to update")

    return option_parser.parse_args()

def add_to_db(cursor, level, db):
    """add cursor indexer to db
    """
    if cursor.kind == CursorKind.CALL_EXPR and \
            len(list(cursor.get_children())) > 0:
        return
    if not isinstance(cursor, Cursor) or cursor.location.file is None:
        return
    usr = get_usr_of_declaration_cursor(cursor)
    if usr is None or usr == "":
        return
    value_string = "%s::%s::%s" % \
            (os.path.abspath(cursor.location.file.name), cursor.location.line, \
            cursor.location.column)
    if db.has_key(usr):
        value_former = db[usr]
        if value_string in value_former:
            return
        value_string = value_former + "," + value_string
    db[usr] = value_string

def add_indexer_for_file(filename, db):
    """paser file with filename and add its indexers to db
    """
    print "parse file %s" % filename
    tu_source = get_tu(filename)
    assert(isinstance(tu_source, TranslationUnit))
    if check_diagnostics(tu_source.diagnostics):
        print "diagnostics occurs, parse result may be incorrect"
    walk_ast(tu_source, partial(add_to_db, db = db))

def main():
    """ main function, parse input and add indexer to db
    """
    db_filename = os.path.join(os.path.expanduser("~"), "test.db")
    options, args = parse_options()

    if options.filename is None and options.directory is None:
        print "please input filename or directory"
        sys.exit(-1)

    db = bsddb.btopen(db_filename, "c")

    if options.filename is not None and os.path.isfile(options.filename):
        add_indexer_for_file(options.filename, db)

    if options.directory is not None and os.path.isdir(options.directory):
        scan_dir_parse_files(options.directory, \
                partial(add_indexer_for_file, db = db))

    db.close()

if __name__ == "__main__":
    main()
