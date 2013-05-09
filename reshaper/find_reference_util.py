"""util functions for finding reference
"""
import os, sys
from clang.cindex import Cursor
from clang.cindex import CursorKind
from reshaper.util import get_tu, check_diagnostics
from reshaper.semantic import get_declaration_cursor
from reshaper.semantic import get_cursors_add_parent
from reshaper.option import setup_find_reference_options
from optparse import OptionParser
import reshaper.option

def get_usr_of_declaration_cursor(cursor):
    """get declaration cursor and return its USR
    """
    declaration_cursor = get_declaration_cursor(cursor)
    if isinstance(declaration_cursor, Cursor):
        return declaration_cursor.get_usr()
    return None

def filter_cursors_by_usr(cursors, target_usr):
    """the input cursors are gotten from tu only by its spelling and 
    displayname, so there may be many fake ones that with the same
    displayname but not the referece we want.
    Then, we need to remove the fake cursors by usr and return the 
    cursors we want.
    """
    cursor_dict = {}
    for cursor in cursors:
        if cursor.kind == CursorKind.CALL_EXPR and \
           len(list(cursor.get_children())) > 0:
            continue
        
        cursor_usr = get_usr_of_declaration_cursor(cursor)
        
        #FIXME:template class and template function;
        #its declaration USR is different from USR 
        if cursor_usr == target_usr:
            location = cursor.location
            key = (os.path.abspath(location.file.name), location.line, location.column)
            cursor_dict[key] = cursor

    return [cursor for cursor in cursor_dict.itervalues()]

def get_cursors_with_name(file_name, name, ref_curs):
    """call back pass to semantic.scan_dir_parse_files 
       to parse files
    """
    if not os.path.exists(file_name):
        print "file %s don't exists\n" % file_name
        return
    current_tu = get_tu(file_name)
    if check_diagnostics(current_tu.diagnostics):
        print "Warning : diagnostics occurs, skip file %s" % file_name
        return

    cursors = get_cursors_add_parent(current_tu, name)
    #don't forget to define global _refer_curs'
    ref_curs.extend(cursors)


def parse_find_reference_args(default_output_filename):
    '''get user options and parse it for 
    finding reference
    '''
    option_parser = OptionParser(usage = "%prog [options]")
    setup_find_reference_options(option_parser)
    options, args = option_parser.parse_args()

    #check input args
    if options.filename is None:
        option_parser.error("please input file to search")
    
    if not os.path.isfile(options.filename):
        option_parser.error("file %s is not exists, please check it!" % options.filename)

    if options.spelling is None:
        option_parser.error("please input reference spelling")

    if options.line is None:
        option_parser.error("please input reference line No.")

    if options.column is None:
        print "Warning : forget to input column",
        print ", the first one in %s line %s will be used" \
                % (options.filename, options.line)

    if options.output_file_name is not None\
            and not os.path.isfile(options.output_file_name):
        tmp_output_file = os.path.join(".", \
                default_output_filename)
        print "Warning : output_file_name %s don't exists" \
                % options.output_file_name,
        print "will create one under current directory :%s"\
                % tmp_output_file
        options.output_file_name = tmp_output_file 

    return options
 
