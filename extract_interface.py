#! /usr/bin/env python

""" This tool is used to extract interface from a source/header file.
The result will be output to stdout.

Usage: extract_interface.py class.cpp class_name

"""

from clang.cindex import CursorKind
import sys
import os
from reshaper.util import get_tu, get_cursor, get_cursors_if, get_cursor_if
from reshaper.extract import extract_interface
from reshaper import semantic
from optparse import OptionParser


def parse_options():
    """ parse the command line options and arguments and returns them
    """

    option_parser = OptionParser(usage = "%prog [options] FILE CLASSNAME")
    option_parser.add_option("-m", "--methods", dest = "methods",
                             type = "string",
                             help = "Names of methods you want to extract")
    option_parser.add_option("--from-function", dest = "from_function",
                             type = "string",
                             help = "Name of the function that uses CLASSNAME")
    option_parser.add_option("--from-class", dest = "from_class",
                             type = "string",
                             help = "Name of the class that uses CLASSNAME")

    # handle option or argument error.
    options, args = option_parser.parse_args()
    return option_parser, options, args

    
def main():
    option_parser, options, args = parse_options()
    if len(args) != 2:
        option_parser.error("Please input source file and class name.")

    src, class_to_extract = args
    if not os.path.exists(src):
        option_parser.error("Source file doesn't exist: %s" % src)

    # --from-function and --from-class are mutual exclusive
    if options.from_function and options.from_class:
        option_parser.error("options --from-function and"
                            " --from-class are mutually exclusive")
        
    methods = options.methods
    if methods is not None:
        methods = methods.split(',')

    _tu = get_tu(src)
    # TODO: the following line should be changed to work on class in a namespace
    class_cursor = get_cursor_if(_tu,
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
    fun_using_class = options.from_function
    if fun_using_class is not None:
        fun_cursor = get_cursor_if(_tu,
                                   lambda c: c.spelling == fun_using_class and
                                       c.is_definition())
        methods = semantic.get_class_usage_from_fun(
            fun_cursor, class_to_extract)

    cls_using_class = options.from_class
    if cls_using_class is not None:
        cls_cursor = get_cursor_if(_tu,
                                   lambda c: c.spelling == cls_using_class and
                                       c.is_definition())
        methods = semantic.get_class_usage_from_cls(cls_cursor, class_to_extract)

    # print out the interface class
    class_printer = extract_interface(class_cursor, methods)
    print class_printer.get_definition()
        

if __name__ == '__main__':
    main()
        
