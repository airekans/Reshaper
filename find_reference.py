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
from reshaper.util import get_tu
from reshaper.util import get_cursor_with_location
import reshaper.semantic as semantic_util
from functools import partial
from optparse import OptionParser

_refer_curs = []

def parse_options():
    """ parse the command line options and arguments and returns them
    """

    option_parser = OptionParser(usage = "%prog [options]")
    option_parser.add_option("-f", "--file", dest = "filename",
                             type = "string",
                             help = "Names of file to find reference")
    option_parser.add_option("-s", "--spelling", dest = "spelling",
                             type = "string",
                             help = "spelling of target to find reference")
    option_parser.add_option("-l", "--line", dest = "line",
                             type = "int",
                             help = "line of target to find reference")
    option_parser.add_option("-c", "--column", dest = "column",
                             type = "int",
                             help = "column of target to find reference",
                             default = None)
    option_parser.add_option("-d", "--directory", dest = "directory",
                             type = "string",
                             help = "directory to search for finding reference",
                             default = ".")
    option_parser.add_option("-o", "--output-file", dest = "output_file_name",
                             type = "string",
                             help = "output file name")

    return option_parser.parse_args()

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
            cur_parent = semantic_util.get_calling_function(cur)
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

def get_usr_of_declaration_cursor(cursor):
    """get declaration cursor and return its USR
    """
    declaration_cursor = semantic_util.get_declaration_cursor(cursor)
    if isinstance(declaration_cursor, Cursor):
        return declaration_cursor.get_usr()
    return None

def get_cursors_with_name(file_name, name):
    """call back pass to semantic.scan_dir_parse_files 
       to parse files
    """
    if not os.path.exists(file_name):
        print "file %s don't exists\n" % file_name
        return
    current_tu = get_tu(file_name)
    if semantic_util.check_diagnostics(current_tu.diagnostics):
        print "Warning : diagnostics occurs, skip file %s" % file_name
        return

    cursors = semantic_util.get_cursors_add_parent(current_tu, name)
    #don't forget to define global _refer_curs'
    _refer_curs.extend(cursors)

def filter_cursors_by_usr(cursors, target_usr):
    """the input cursors are gotten from tu only by its spelling and 
    displayname, so there may be many fake ones that with the same
    displayname but not the referece we want.
    Then, we need to remove the fake cursors by usr and return the 
    cursors we want.
    """
    curs_dic = {}
    for cur in cursors:
        if cur.kind == CursorKind.CALL_EXPR and \
                len(list(cur.get_children())) > 0:
            continue 
        cursor_usr = get_usr_of_declaration_cursor(cur)
        
        #FIXME:template class and template function;
        #its declaration USR is different from USR 
        if cursor_usr == target_usr:
            curs_dic["%s%s%s" % (\
                    os.path.abspath(cur.location.file.name), \
                    cur.location.line, cur.location.column)] = cur

    keys = curs_dic.keys()
    keys.sort()
    return [curs_dic[key] for key in keys]

def main():
    '''main function of find reference
    '''
    options, args = parse_options()

    #check input args
    if not os.path.isfile(options.filename):
        print "file %s is not exists, please check it!" % options.filename
        sys.exit(-1)

    if options.spelling is None:
        print "please input reference spelling"
        sys.exit(-1)

    if options.line is None:
        print "please input reference line No."
        sys.exit(-1)

    if options.column is None:
        print "Warning : forget to input column",
        print ", the first one in %s line %s will be chosen" \
                % (options.filename, options.line)

    if options.output_file_name is not None\
            and not os.path.isfile(options.outputFile):
        tmp_output_file = os.path.join(os.path.dirname(__file__), \
                "referenceResult.txt")
        print "Warning : output_file_name %s don't exists" \
                % options.output_file_name,
        print "will create one under current directory :%s"\
                % tmp_output_file
        options.output_file_name = tmp_output_file 
     
    #get target reference info
    tu_source = get_tu(os.path.abspath(options.filename))
    assert(isinstance(tu_source, TranslationUnit))

    if semantic_util.check_diagnostics(tu_source.diagnostics):
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
    
    #parse input directory
    semantic_util.scan_dir_parse_files(options.directory, \
            partial(get_cursors_with_name, name = options.spelling))
    final_output = filter_cursors_by_usr(_refer_curs, reference_usr)

    #output result
    if options.output_file_name:
        output_to_file(target_cursor, final_output, options.output_file_name)
    else:
        output_string = get_output_string(target_cursor, final_output)
        print output_string

if __name__ == "__main__":
    main()

