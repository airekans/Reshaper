#! /usr/bin/env python

from clang.cindex import CursorKind
from clang.cindex import TranslationUnit
from clang.cindex import TypeKind
from clang.cindex import Cursor
from clang.cindex import Type
import os
import sys
from util import get_cursor


def get_function_signature(m):
    tokens = list(m.get_tokens())
    if len(tokens) < 1:
        return ""

    extent = tokens[0].extent
    line, column = extent.end.line, extent.end.column
    signature = tokens[0].spelling
    for t in tokens[1:]:
        e = t.extent
        if line != e.start.line:
            for i in range(0, e.start.line - line):
                signature += "\n"
            line = e.start.line
            if e.start.column < column:
                column = e.start.column
        
        for i in range(0, e.start.column - column):
            signature += " "

        signature += t.spelling
        line, column = extent.end.line, extent.end.column

    return signature
            
    

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print "Please input .cpp file and class."
        sys.exit(1)
    
    source_dir = os.path.join(os.path.dirname(__file__), 'test_data')
    src = os.path.join(source_dir, sys.argv[1])
    class_to_extract = sys.argv[2]

    tu = TranslationUnit.from_source(src)
    class_cursor = get_cursor(tu, class_to_extract)
    
    if class_cursor is None or \
            class_cursor.kind != CursorKind.CLASS_DECL or \
            not class_cursor.is_definition():
        print "source file %s does not contain any class" % src
        sys.exit(1)

    member_cursors = list(class_cursor.get_children())

    member_method_cursors = [m for m in member_cursors
                             if m.kind == CursorKind.CXX_METHOD]

    for m in member_method_cursors:
        print "name of the member:", m.spelling
        print "displayname:", m.displayname
        print "kind:", m.kind.name
        print "type name:", m.type.kind.spelling

        print get_function_signature(m)
        tokens = m.get_tokens()
        for i, t in enumerate(tokens):
            print "token[%d]: %s" % (i, t.spelling)
#            print "token loc:", t.extent

        arg_types = m.type.argument_types()
        result_type = m.result_type
        result_type_spelling = result_type.kind.spelling.lower()

        print "  result type:", result_type.kind.name
        print "  result spelling:", result_type_spelling

        for arg in arg_types:
            print "  arg type:", arg.kind.name


        
            
        print
    


