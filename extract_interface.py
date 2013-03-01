#! /usr/bin/env python

""" This tool is used to extract interface from a source/header file.
The result will be output to stdout.

Usage: extract_interface.py class.cpp class_name

"""

from clang.cindex import CursorKind
from clang.cindex import TranslationUnit
from clang.cindex import Cursor
import sys
from util import get_cursor, get_cursors_if


def get_function_signature(fun):
    tokens = list(fun.get_tokens())
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
            for _ in range(0, e.start.line - line):
                signature += "\n"
            line = e.start.line
            if e.start.column < column:
                column = e.start.column
        
        for _ in range(0, e.start.column - column):
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

    def __get_default_destructor(self):
        return "virtual ~%s {}" % self._name

    def __get_virtual_method(self, method):
        if method.startswith("virtual"):
            return method
        else:
            return "virtual " + method
            
    def __get_pure_virtual_method(self, method):
        virtual_method = self.__get_virtual_method(method)
        if virtual_method.endswith("0"):
            return virtual_method
        else:
            return virtual_method + " = 0"

    def __get_pure_virtual_signature(self, method):
        return self.__get_pure_virtual_method(get_function_signature(method))

    def set_methods(self, methods):
        self._methods = methods

    def set_members(self, members):
        self._members = members

    def get_forward_declaration(self):
        return self.__get_declaration() + ";"

    def get_definition(self):
        indent = "    "
        method_signatures = [get_function_signature(m) for m in self._methods]
        methods = "\n".join([indent + self.__get_default_destructor()] +
                            [indent + self.__get_pure_virtual_method(m) + ";"
                             for m in method_signatures
                             if not m.startswith(("template", "static"))])
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
    print "class name:", class_cursor.spelling
    class_printer = ClassPrinter("I" + class_cursor.spelling)
    class_printer.set_methods(member_method_cursors)

    print class_printer.get_definition()
        
