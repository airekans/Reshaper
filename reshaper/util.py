# This file provides common utility functions for the test suite.

from clang.cindex import Cursor
from clang.cindex import CursorKind
from clang.cindex import TranslationUnit
import ConfigParser
import os
from functools import partial

def get_tu(source, all_warnings=False):
    """Obtain a translation unit from source and language.

    By default, the translation unit is created from source file "t.<ext>"
    where <ext> is the default file extension for the specified language. By
    default it is C, so "t.c" is the default file name.

    all_warnings is a convenience argument to enable all compiler warnings.
    """
    args = ['-x', 'c++', '-std=c++11']
 
    if all_warnings:
        args += ['-Wall', '-Wextra']

    config_parser = ConfigParser.SafeConfigParser()
    config_parser.read(['.reshaper.cfg', os.path.expanduser('~/.reshaper.cfg')])
    if config_parser.has_option('Clang Options', 'include_paths'):
        include_paths = config_parser.get('Clang Options', 'include_paths')
        args += ['-I' + p for p in include_paths.split(',')]

    return TranslationUnit.from_source(source, args)

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

def get_cursor_with_location(tu, spelling, line, column = None):
    '''Get specific cursor by line and column
    '''
    def check_cursor_spelling_displayname(cursor, spelling):
        if cursor.is_definition() and cursor.spelling == spelling:
                return True
        elif spelling in cursor.displayname:
                return True
        return False

    alternate_cursors = get_cursors_if(tu, partial(check_cursor_spelling_displayname, spelling = spelling))
    for cursor in alternate_cursors:
        if cursor.kind == CursorKind.CALL_EXPR and \
                len(list(cursor.get_children())) > 0:
            continue
        if column is not None:
            if cursor.location.line == line and \
                    cursor.location.column == column:
                return cursor
        else:
            if cursor.location.line == line:
                return cursor
    return None

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
    start_column = extent.start.column
    line, column = extent.end.line, extent.end.column
    signature = valid_tokens[0].spelling
    for t in valid_tokens[1:]:
        e = t.extent
        if line != e.start.line:
            signature += "\n" * (e.start.line - line)
            if e.start.column < start_column:
                column = e.start.column
            else:
                column = start_column
        
        signature += " " * (e.start.column - column)
        signature += t.spelling
        line, column = e.end.line, e.end.column

    return signature

