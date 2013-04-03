#!/usr/bin/env python

"""find_call_chain.py -- find call chains of specific word \
example: input  :C
         output  : A -> B -> C ; means A call B , B call C
"""

import sys
from clang.cindex import Cursor
from clang.cindex import CursorKind
from clang.cindex import TranslationUnit
from reshaper.util import get_tu
from reshaper.util import get_cursor_with_location
import reshaper.semantic as semantic_util
from functools import partial
from reshaper.find_reference_util import get_usr_of_declaration_cursor
from reshaper.find_reference_util import filter_cursors_by_usr
from reshaper.find_reference_util import get_cursors_with_name
from reshaper.find_reference_util import parse_find_reference_args

_global_usr = []
_output_file_contents = "digraph G{\n"
_search_directory = None

def get_cursor_info(cursor):
    '''use to get semantic_parent.spelling :: cursor.spelling or displayname 
    infomation of the input cursors;
    for example: TestUSR::test_decla(int), MyNameSpace::test_defin(double)
    or test_function(TestUSR&)
    '''
    seman_parent = semantic_util.get_semantic_parent_of_decla_cursor(cursor)
    out_str = cursor.displayname
    if out_str == None:
        out_str = cursor.spelling

    if seman_parent is not None and \
            (seman_parent.kind == CursorKind.NAMESPACE or\
            seman_parent.kind == CursorKind.CLASS_DECL):
        return "%s::%s" % (seman_parent.spelling, out_str)
    else:
        return out_str

def find_reference_update_output_contents(target_cursor):
    '''this function is used to find reference of the target_cursor,
    , format its infomation together with calling function info, which
    will be write to _output_file_contents
    '''
    reference_usr = get_usr_of_declaration_cursor(target_cursor)
    global _global_usr
    _global_usr.append(reference_usr)
    spelling_value = ""
    if target_cursor.is_definition():
        spelling_value = (target_cursor.spelling.split('('))[0]
    else:
        spelling_value = (target_cursor.displayname.split('('))[0]

    refer_curs = []
    global _search_directory
    semantic_util.scan_dir_parse_files(_search_directory, \
            partial(get_cursors_with_name, \
            name = spelling_value, \
            ref_curs = refer_curs))
    final_output = filter_cursors_by_usr(refer_curs, reference_usr)

    target_info = get_cursor_info(target_cursor)

    for cursor in final_output:
        calling_cursor = semantic_util.get_calling_function(cursor)
        if calling_cursor is not None:
            calling_info = get_cursor_info(calling_cursor)
            global _output_file_contents 
            _output_file_contents += "\"%s\" -> \"%s\";\n" % \
                    (calling_info, target_info)

    return final_output

def handle_output_result(iutput_cursors):
    '''this function will recursively handle the calling function 
    cursors of the input_cursors list, which is not handled
    before (use _global_usr to judge if a cursor is handled already)
    '''
    for cur in iutput_cursors:
        assert(isinstance(cur, Cursor))
        calling_cursor = semantic_util.get_calling_function(cur)
        if calling_cursor is None:
            continue
        cur_usr = get_usr_of_declaration_cursor(calling_cursor)
        global _global_usr
        if cur_usr not in set(_global_usr):
            output_curs = find_reference_update_output_contents(calling_cursor)
            handle_output_result(output_curs)

def output_to_file(file_name):
    '''write _output_file_contents to file
    '''
    file_handle = open(file_name, "w")
    file_handle.write(_output_file_contents)
    file_handle.close()

def main():
    '''main function : get the user args;
    find reference for the specific word;
    begin to handle its output recursively
    '''
    output_file = "findCallChainResult.txt"
    options = parse_find_reference_args(output_file)
    global _search_directory
    _search_directory = options.directory
    tu_source = get_tu(options.filename)
    assert(isinstance(tu_source, TranslationUnit))

    if semantic_util.check_diagnostics(tu_source.diagnostics):
        print "Error"
        print
        sys.exit(-1)
    target_cursor = get_cursor_with_location(tu_source, \
            options.spelling, \
            options.line, \
            options.column)
    output_curs = find_reference_update_output_contents(target_cursor)
    handle_output_result(output_curs)
    global _output_file_contents
    _output_file_contents += "}\n"

    if options.output_file_name:
        output_to_file(options.output_file_name)
    else:
        print _output_file_contents

if __name__ == "__main__":
    main()

