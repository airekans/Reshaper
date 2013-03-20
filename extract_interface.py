#! /usr/bin/env python

""" This tool is used to extract interface from a source/header file.
The result will be output to stdout.

Usage: extract_interface.py class.cpp class_name

"""

from clang.cindex import CursorKind
from clang.cindex import TranslationUnit
from clang.cindex import Cursor
import sys
from reshaper.util import get_cursor, get_cursors_if
from reshaper.classprinter import ClassPrinter


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print "Please input .cpp file and class."
        sys.exit(1)
    
    SRC = sys.argv[1]
    class_to_extract = sys.argv[2]

    tu = TranslationUnit.from_source(SRC, ["-std=c++11"])
    class_cursor = get_cursor(tu, class_to_extract)
    
    if class_cursor is None or \
            class_cursor.kind != CursorKind.CLASS_DECL or \
            not class_cursor.is_definition():
        print "source file %s does not contain any class" % SRC
        sys.exit(1)

    member_method_cursors = \
        get_cursors_if(class_cursor,
                       lambda c: c.kind == CursorKind.CXX_METHOD)
    
    # print out the interface class
    class_printer = ClassPrinter("I" + class_cursor.spelling)
    class_printer.set_methods(member_method_cursors)

    print class_printer.get_definition()
        
