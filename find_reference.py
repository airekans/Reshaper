#!/usr/bin/env python

"""This tool is used to find reference of specific word
The result will be output to stdout, 
also can be output to a file specified by -o 

Usage : find_reference.py -f test.cpp -l 37 -d . -o sample.txt
"""
import os, sys
from clang.cindex import Cursor
from clang.cindex import CursorKind
from clang.cindex import TranslationUnit
import reshaper.semantic as semantic_util
from reshaper.util import get_tu, check_diagnostics
from reshaper.util import get_cursor_with_location
from reshaper.find_reference_util import get_usr_of_declaration_cursor
from reshaper.find_reference_util import get_cursors_with_name
from reshaper.find_reference_util import filter_cursors_by_usr
from reshaper.find_reference_util import parse_find_reference_args
from functools import partial

def get_output_string(target_cursor, result_cursors):
    """ get output string from result cursors and return it
    """
    output_string = "\n"
    output_string += "Reference of \"%s\": file : %s, location %s %s \n" % \
            (target_cursor.displayname, target_cursor.location.file.name, \
            target_cursor.location.line, target_cursor.location.column)
    for cur in result_cursors:
        if not isinstance(cur, Cursor):
            continue

        output_string += "--------------------------------"
        output_string += "--------------------------------\n "
        output_string += "file : %s \n" % \
                os.path.abspath(cur.location.file.name)
        if cur.kind == CursorKind.CXX_METHOD:
            output_string += "class : %s\n" % cur.semantic_parent.spelling \
                    if cur.semantic_parent is not None else None
        elif cur.kind == CursorKind.FUNCTION_DECL:
            if cur.semantic_parent is not None and\
                    cur.semantic_parent.kind == CursorKind.NAMESPACE:
                output_string += "namespace : %s\n" % \
                        cur.semantic_parent.spelling \
                        if not cur.semantic_parent.spelling == ''\
                        else "anonymouse namespace\n"
            else:
                output_string += "global function\n"

        else:
            cur_parent = semantic_util.get_caller(cur)
            if cur_parent:
                output_string += "Call function:"
                out_str = cur_parent.displayname
                if out_str == None:
                    out_str = cur_parent.spelling
                output_string += out_str
                output_string += "\n"
        output_string += "line %s, column %s\n"\
                % (cur.location.line, cur.location.column)

    return output_string

def output_to_file(target_cursor, curs, file_path):
    """output result to file
    """
    file_handle = open(file_path, "w")
    output_string = get_output_string(target_cursor, curs)
    file_handle.write(output_string)
    file_handle.close()

def main():
    '''main function of find reference
    '''
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
        print "Error : Can't get source cursor" 
        print "please check file:%s, name:%s, line:%s, column:%s "\
                % (options.filename, options.spelling,\
                options.line, options.column)
        sys.exit(-1)

    reference_usr = get_usr_of_declaration_cursor(target_cursor)
    
    #parse input directory
    refer_curs = []
    semantic_util.scan_dir_parse_files(options.directory, \
            partial(get_cursors_with_name, \
                    name = options.spelling, \
                    ref_curs = refer_curs))
    final_output = filter_cursors_by_usr(refer_curs, reference_usr)

    #output result
    if options.output_file_name:
        output_to_file(target_cursor, final_output, options.output_file_name)
    else:
        output_string = get_output_string(target_cursor, final_output)
        print output_string

if __name__ == "__main__":
    main()

