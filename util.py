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
    - `f`: function
    """
    return [c for c in source.get_children() if f(c)]

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
    

__all__ = [
    'get_cursor',
    'get_cursors',
    'get_tu',
]
