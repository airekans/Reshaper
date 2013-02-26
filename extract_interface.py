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

    valid_tokens = []
    for t in tokens:
        if t.spelling in ['{', ';']:
            break
        valid_tokens.append(t)

    extent = valid_tokens[0].extent
    line, column = extent.end.line, extent.end.column
    signature = valid_tokens[0].spelling
    for t in valid_tokens[1:]:
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
        line, column = e.end.line, e.end.column

    return signature


class ClassPrinter(object):
    """ ClassPrinter is used to generate a class in a files
    """
    
    def __init__(self, name):
        """
        
        Arguments:
        - `name`: class name
        """
        self._name = name
        self._methods = []
        self._members = []

    def __get_declaration(self):
        return "class " + self._name

    def set_methods(self, methods):
        self._methods = methods

    def set_members(self, members):
        self._members = members

    def get_forward_declaration(self):
        return self.__get_declaration() + ";"

    def get_definition(self):
        indent = "    "
        methods = "\n".join([indent + get_function_signature(m) + ";"
                             for m in self._methods])
        # TODO: add members

        class_def = """%s
{
public:
%s
};""" % (self.__get_declaration(), methods)
        return class_def
        


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

    member_method_cursors = \
        get_cursors_if(class_cursor,
                       lambda c: c.kind == CursorKind.CXX_METHOD)

    for m in member_method_cursors:
        print "name of the member:", m.spelling
        print "displayname:", m.displayname
        print "kind:", m.kind.name
        print "type name:", m.type.kind.spelling

        print get_function_signature(m)
        tokens = m.get_tokens()

        arg_types = m.type.argument_types()
        result_type = m.result_type
        result_type_spelling = result_type.kind.spelling.lower()

        print "  result type:", result_type.kind.name
        print "  result spelling:", result_type_spelling

        for arg in arg_types:
            print "  arg type:", arg.kind.name
            
        print
    
    # print out the interface class
    print "class name:", class_cursor.spelling
    class_printer = ClassPrinter("I" + class_cursor.spelling)
    class_printer.set_methods(member_method_cursors)

    print class_printer.get_definition()
        
