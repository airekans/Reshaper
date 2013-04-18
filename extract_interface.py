#! /usr/bin/env python

""" This tool is used to extract interface from a source/header file.
The result will be output to stdout.

Usage: extract_interface.py class.cpp class_name

"""

from clang.cindex import CursorKind
from clang.cindex import TranslationUnit
import sys
import os
from reshaper.util import get_tu, get_cursor, get_cursors_if
from reshaper.extract import extract_interface
from optparse import OptionParser


def parse_options():
    """ parse the command line options and arguments and returns them
    """

    option_parser = OptionParser(usage = "%prog [options] FILE CLASSNAME")
    option_parser.add_option("-m", "--methods", dest = "methods",
                             type = "string",
                             help = "Names of methods you want to extract")
    option_parser.add_option("--from-usage", dest = "from_usage",
                             type = "string",
                             help = "Name of the function that using CLASSNAME")

    return option_parser.parse_args()

def get_member_owner(member_cursor):
    """ Get the owner of the member given as cursor
    
    Arguments:
    - `member_cursor`:
    """

    if member_cursor.kind != CursorKind.MEMBER_REF_EXPR:
        return None

    for c in member_cursor.get_children():
        return c

    return None


def get_class_usage(fun_cursor, used_class):
    """ get the usage of the class from the function given as fun_cursor.
    """

    if not fun_cursor.is_definition():
        return []

    # get all member function calls
    def is_member_fun_call(c):
        if c.kind != CursorKind.CALL_EXPR:
            return False

        for child in c.get_children():
            return child.kind == CursorKind.MEMBER_REF_EXPR

        return False
        
    # get all member function calls in the function
    get_cursors_if(fun_cursor, is_member_fun_call)

    
    
def main():
    options, args = parse_options()
    if len(args) != 2:
        print "Please input source file and class name."
        sys.exit(1)

    src, class_to_extract = args
    if not os.path.exists(src):
        print "Source file doesn't exist: %s" % src
        sys.exit(1)
    
    methods = options.methods
    if methods is not None:
        methods = methods.split(',')

    tu = get_tu(src)
    # TODO: the following line should be changed to work on class in a namespace
    class_cursor = get_cursor(tu, class_to_extract)
    
    if class_cursor is None or \
            class_cursor.kind != CursorKind.CLASS_DECL or \
            not class_cursor.is_definition():
        print "source file %s does not contain any class named %s" % \
            (src, class_to_extract)
        sys.exit(1)

    # If user specifies to extract a class from other function's usage,
    # analyze the function
    fun_using_class = options.from_usage
    if fun_using_class is not None:
        pass

    # print out the interface class
    class_printer = extract_interface(class_cursor, methods)
    print class_printer.get_definition()
        

if __name__ == '__main__':
    main()
        
