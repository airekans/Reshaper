#! /usr/bin/env python

""" This tool is used to extract interface from a source/header file.
The result will be output to stdout.

Usage: extract_interface.py class.cpp class_name

"""

from clang.cindex import CursorKind
from clang.cindex import TranslationUnit
import sys
import os
from reshaper.util import get_tu, get_cursor, get_cursors_if, get_cursor_if
from reshaper.semantic import get_semantic_parent_of_decla_cursor, get_declaration_cursor
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
    member_fun_calls = get_cursors_if(fun_cursor, is_member_fun_call)
    target_member_fun_calls = \
        [c for c in member_fun_calls
         if get_semantic_parent_of_decla_cursor(c).spelling == used_class]
    target_member_funs = \
        [get_declaration_cursor(c) for c in target_member_fun_calls]
    method_names = [c.spelling for c in target_member_funs]
    return set(method_names)
    
    
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
    class_cursor = get_cursor_if(tu,
                                 lambda c: c.spelling == class_to_extract
                                     and c.is_definition())
    
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
        fun_cursor = get_cursor_if(tu, lambda c: c.spelling == fun_using_class and c.is_definition())
        methods = get_class_usage(fun_cursor, class_to_extract)
        
    # print out the interface class
    class_printer = extract_interface(class_cursor, methods)
    print class_printer.get_definition()
        

if __name__ == '__main__':
    main()
        
