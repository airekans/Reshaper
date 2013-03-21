#! /usr/bin/env python

""" This tool is used to extract interface from a source/header file.
The result will be output to stdout.

Usage: extract_interface.py class.cpp class_name

"""

from clang.cindex import CursorKind
from clang.cindex import TranslationUnit
from clang.cindex import Cursor
import sys
import os
from reshaper.util import get_cursor, get_cursors_if
from reshaper.classprinter import ClassPrinter
from optparse import OptionParser


def extract_interface(class_cursor, methods, prefix = "I"):
    """ extract interface from an given class.
    Returns a ClassPrinter representing the interface.
    The default interface name is "I" followed by the class name.
    e.g. class name is "Base", then the interface name is IBase.
    
    Arguments:
    - `class_cursor`: cursor of the class to be extracted
    - `methods`: methods user wants to extract to the interface
    - `prefix`: the interface name prefix used to prepend to the class name
    """

    member_method_cursors = \
        get_cursors_if(class_cursor,
                       lambda c: (c.kind == CursorKind.CXX_METHOD and
                                  (c.spelling in methods
                                   if methods is not None else True)))
    
    # print out the interface class
    class_printer = ClassPrinter(prefix + class_cursor.spelling)
    class_printer.set_methods(member_method_cursors)
    return class_printer
    

def parse_options():
    """ parse the command line options and arguments and returns them
    """

    option_parser = OptionParser(usage = "%prog [options] FILE CLASSNAME")
    option_parser.add_option("-m", "--methods", dest = "methods", type = "string",
                             help = "Names of methods you want to extract")

    return option_parser.parse_args()

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

    tu = TranslationUnit.from_source(src, ["-std=c++11"])
    # TODO: the following line should be changed to work on class in a namespace
    class_cursor = get_cursor(tu, class_to_extract)
    
    if class_cursor is None or \
            class_cursor.kind != CursorKind.CLASS_DECL or \
            not class_cursor.is_definition():
        print "source file %s does not contain any class named %s" % \
            (src, class_to_extract)
        sys.exit(1)

    # print out the interface class
    class_printer = extract_interface(class_cursor, methods)
    print class_printer.get_definition()
        

if __name__ == '__main__':
    main()
        
