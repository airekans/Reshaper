# This file provides common utility functions for the test suite.

from clang.cindex import Cursor
from clang.cindex import TranslationUnit

def get_tu(source, lang='c', all_warnings=False):
    """Obtain a translation unit from source and language.

    By default, the translation unit is created from source file "t.<ext>"
    where <ext> is the default file extension for the specified language. By
    default it is C, so "t.c" is the default file name.

    Supported languages are {c, cpp, objc}.

    all_warnings is a convenience argument to enable all compiler warnings.
    """
    name = 't.c'
    args = []
    if lang == 'cpp':
        name = 't.cpp'
        args.append('-std=c++11')
    elif lang == 'objc':
        name = 't.m'
    elif lang != 'c':
        raise Exception('Unknown language: %s' % lang)

    if all_warnings:
        args += ['-Wall', '-Wextra']

    return TranslationUnit.from_source(name, args, unsaved_files=[(name,
                                       source)])

def get_cursor(source, spelling):
    """Obtain a cursor from a source object.

    This provides a convenient search mechanism to find a cursor with specific
    spelling within a source. The first argument can be either a
    TranslationUnit or Cursor instance.

    If the cursor is not found, None is returned.
    """
    children = []
    if isinstance(source, Cursor):
        children = source.get_children()
    else:
        # Assume TU
        children = source.cursor.get_children()

    for cursor in children:
        if cursor.spelling == spelling:
            return cursor

        # Recurse into children.
        result = get_cursor(cursor, spelling)
        if result is not None:
            return result

    return None
 
def get_cursors(source, spelling):
    """Obtain all cursors from a source object with a specific spelling.

    This provides a convenient search mechanism to find all cursors with specific
    spelling within a source. The first argument can be either a
    TranslationUnit or Cursor instance.

    If no cursors are found, an empty list is returned.
    """
    cursors = []
    children = []
    if isinstance(source, Cursor):
        children = source.get_children()
    else:
        # Assume TU
        children = source.cursor.get_children()

    for cursor in children:
        if cursor.spelling == spelling:
            cursors.append(cursor)

        # Recurse into children.
        cursors.extend(get_cursors(cursor, spelling))

    return cursors

def get_cursors_if(source, f):
    """ Get cursors satisfying function f from cursor c
    
    Arguments:
    - `source`: 
    - `f`: predicate function user gives
    """
    cursors = []
    children = []
    if isinstance(source, Cursor):
        children = source.get_children()
    else:
        # Assume TU
        children = source.cursor.get_children()

    for child in children:
        if f(child):
            cursors.append(child)

        cursors.extend(get_cursors_if(child, f))

    return cursors

def walk_ast(source, f):
    """walk the ast with the specified function
    
    Arguments:
    - `source`: 
    - `f`: function used to visit the cursor
    """

    if source is None:
        return
    elif isinstance(source, Cursor):
        cursor = source
    else: 
        # Assume TU
        cursor = source.cursor

    def walk_ast_with_level(cursor, level):
        f(cursor, level)
        child_level = level + 1
        for c in cursor.get_children():
            walk_ast_with_level(c, child_level)

    walk_ast_with_level(cursor, 0)

def get_function_signature(fun):
    """get the signature of the function given as a cursor node in the AST.
    """
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

