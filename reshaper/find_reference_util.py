"""util functions for finding reference
"""
import os, sys
from clang.cindex import CursorKind
from reshaper.util import  check_diagnostics
from reshaper.ast import get_tu
from reshaper.semantic import get_cursors_add_parent, is_cursor
from optparse import OptionParser

def get_usr_of_declaration_cursor(cursor):
    """get declaration cursor and return its USR
    """
    declaration_cursor = cursor.get_declaration()
    if is_cursor(declaration_cursor):
        return declaration_cursor.get_usr()
    return None

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
            curs_dic[os.path.abspath(cur.location.file.name), cur.location.line, cur.location.column]= cur

    keys = curs_dic.keys()
    keys.sort()
    return [curs_dic[key] for key in keys]

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
       # return

    cursors = get_cursors_add_parent(current_tu, name)
    #don't forget to define global _refer_curs'
    ref_curs.extend(cursors)

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

def parse_find_reference_args(default_output_filename):
    '''get user options and parse it for 
    finding reference
    '''
    options, args = parse_options()

    #check input args
    if options.filename is None or not os.path.isfile(options.filename):
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

    if options.output_file_name is not None:
        try:
            file_handle = open(options.output_file_name, 'w')
        except IOError, e:
            print e
            tmp_output_file = os.path.join(".", \
                default_output_filename)
            print "Error occurs, default output file %s will be used"\
                % tmp_output_file
            options.output_file_name = tmp_output_file 

    return options
 
