#!/usr/bin/env python

"""This tool is used to find reference of specific word 
through indexer db created before.
The result will be output to stdout, 
also can be output to a file specified by -o 

Usage : find_reference.py -f test.cpp -l 37 -d . -o sample.txt
"""

import os, sys
import bsddb
from clang.cindex import TranslationUnit
from reshaper.semantic import check_diagnostics
from reshaper.util import get_tu
from reshaper.util import get_cursor_with_location
from reshaper.find_reference_util import get_usr_of_declaration_cursor
from reshaper.find_reference_util import parse_find_reference_args

def find_reference_from_db(filename, usr):
    """find reference of specific usr in db
    """
    if usr is None:
        return None
    db = bsddb.btopen(filename, "c")
    refer_values = None
    for key in db.keys():
        if usr == key:
            refer_values = db[key]
            break
    db.close()
    return refer_values


def main():
    '''main function of find reference through indexer db
    '''
    db_filename = os.path.join(os.path.expanduser("~"), "test.db")

    output_file = "referenceResult.txt"
    options = parse_find_reference_args(output_file)
    #get target reference info
    tu_source = get_tu(os.path.abspath(options.filename))
    assert(isinstance(tu_source, TranslationUnit))

    if check_diagnostics(tu_source.diagnostics):
        print "Warning : file %s, diagnostics occurs" % options.filename,
        print " parse result may be incorrect!"

    target_cursor = get_cursor_with_location(tu_source, \
            options.spelling, \
            options.line, options.column)
    if not target_cursor:
        print "Error : Can't get source cursor", 
        print "please check file:%s, name:%s, line:%s, column:%s "\
                % (options.filename, options.spelling,\
                options.line, options.column)
        sys.exit(-1)
    reference_usr = get_usr_of_declaration_cursor(target_cursor)
    ref_results = find_reference_from_db(db_filename, reference_usr)
    if ref_results is None:
        return

    results_list = ref_results.split(",")
    results_list.sort()

    output_string = "Reference of \"%s\": file : %s, location %s %s \n" % \
            (target_cursor.displayname, target_cursor.location.file.name, \
            target_cursor.location.line, target_cursor.location.column)
    output_string += "-------------------------------------------------------\n"

    for result in results_list:
        output_string += result
        output_string += "\n"

    print output_string
    
if __name__ == "__main__":
    main()

