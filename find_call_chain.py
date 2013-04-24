#!/usr/bin/env python

"""find_call_chain.py -- find call chains of specific word
example: input  :C
         output  : A -> B -> C ; means A call B , B call C
"""
import sys
from clang.cindex import Cursor
from clang.cindex import TranslationUnit
from reshaper.util import get_tu, check_diagnostics
from reshaper.util import get_cursor_with_location
from reshaper.semantic import get_full_qualified_name
import reshaper.semantic as semantic_util
from functools import partial
from reshaper.find_reference_util import get_usr_of_declaration_cursor
from reshaper.find_reference_util import filter_cursors_by_usr
from reshaper.find_reference_util import get_cursors_with_name
from reshaper.find_reference_util import parse_find_reference_args


def find_reference_update_output_contents(target_cursor, \
        search_directory, global_usr_list, output_contents):
    '''this function is used to find reference of the target_cursor,
    , format its infomation together with calling function info, which
    will be write to output_contents
    '''
    reference_usr = get_usr_of_declaration_cursor(target_cursor)
    global_usr_list.append(reference_usr)
    spelling_value = ""
    if target_cursor.is_definition():
        spelling_value = (target_cursor.spelling.split('('))[0]
    else:
        spelling_value = (target_cursor.displayname.split('('))[0]

    refer_curs = []
    semantic_util.scan_dir_parse_files(search_directory, \
            partial(get_cursors_with_name, \
            name = spelling_value, \
            ref_curs = refer_curs))
    final_output = filter_cursors_by_usr(refer_curs, reference_usr)

    target_info = get_full_qualified_name(target_cursor)

    for cursor in final_output:
        calling_cursor = semantic_util.get_caller(cursor)
        if calling_cursor is not None:
            calling_info = get_full_qualified_name(calling_cursor)
            output_contents.append("\"%s\" -> \"%s\";\n" % \
                    (calling_info, target_info))

    return final_output

def handle_output_result(iuput_cursors, search_directory, \
        global_usr_list, output_contents):
    '''this function will recursively handle the calling function 
    cursors of the input_cursors list, which is not handled
    before (use global_usr_list to judge if a cursor is handled already)
    '''
    for cur in iuput_cursors:
        assert(isinstance(cur, Cursor))
        calling_cursor = semantic_util.get_caller(cur)
        if calling_cursor is None:
            continue
        cur_usr = get_usr_of_declaration_cursor(calling_cursor)
        if cur_usr not in global_usr_list:
            output_curs = find_reference_update_output_contents(calling_cursor, \
                    search_directory, global_usr_list, output_contents)
            handle_output_result(output_curs, search_directory, \
                    global_usr_list, output_contents)

def output_to_file(file_name, contents):
    '''write contents to file
    '''
    file_handle = open(file_name, "w")
    file_handle.write(contents)
    file_handle.close()

def conver_list_to_output_string(output_contents):
    output_string = "digraph G{\n"
    for element in output_contents:
        output_string += element
    output_string += "}\n"
    return output_string

def main():
    '''main function : get the user args;
    find reference for the specific word;
    begin to handle its output recursively
    '''
    output_file = "findCallChainResult.txt"
    options = parse_find_reference_args(output_file)
    tu_source = get_tu(options.filename)
    assert(isinstance(tu_source, TranslationUnit))

    if check_diagnostics(tu_source.diagnostics):
        print "Error"
        print
        sys.exit(-1)
    target_cursor = get_cursor_with_location(tu_source, \
            options.spelling, \
            options.line, \
            options.column)

    global_usr_list  = []

    output_file_contents_list = []

    output_curs = find_reference_update_output_contents(target_cursor, \
            options.directory, global_usr_list, output_file_contents_list)
    handle_output_result(output_curs, options.directory, global_usr_list, output_file_contents_list)

    output_file_contents = conver_list_to_output_string(output_file_contents_list)

    if options.output_file_name:
        output_to_file(options.output_file_name, output_file_contents)
    else:
        print output_file_contents

if __name__ == "__main__":
    main()

