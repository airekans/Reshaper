"""util functions for find Reference 
"""

import os
from clang.cindex import Cursor
from clang.cindex import CursorKind
from clang.cindex import TypeKind
from clang.cindex import Config


_file_types = ('.cpp', '.c', '.cc')
_conf = Config()

def get_cursors_add_parent(source, spelling):
    '''Get Cursors through tu or cursor 
    according to its spelling and displayname
    '''
    children = []
    cursors = []
    if isinstance(source, Cursor):
        children = source.get_children()
    else:
        # Assume TU
        children = source.cursor.get_children()

    for cursor in children:
        if isinstance(cursor, Cursor):
            cursor.parent = source
        if cursor.is_definition():
            if cursor.spelling == spelling:
                cursors.append(cursor)
        else:
            if spelling in cursor.displayname :
                cursors.append(cursor)
        # Recurse into children.
        cursors.extend( get_cursors_add_parent(cursor, spelling))
    return cursors

def scan_dir_parse_files(directory, parse_file):
    '''Scan directory recursivly to 
    get files with file_types
    '''
    for root, dirs, files in os.walk(directory):
        for file_name in files:
            name, file_type = os.path.splitext(file_name)
            if file_type in _file_types:
                parse_file(os.path.join(root, file_name))
        for sub_dir in dirs:
            scan_dir_parse_files(os.path.join(root, sub_dir), parse_file)

def get_cursor_with_location(tu, spelling, line, column = None):
    '''Get specific cursor by line and column
    '''
    alternate_cursors = get_cursors_add_parent(tu, spelling)
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

def get_calling_function(source):
    '''get calling function of source cursor
    '''
    if not isinstance(source, Cursor) or \
            source.parent is None or \
            not isinstance(source.parent, Cursor):
        return None
    elif source.parent.type.kind == TypeKind.FUNCTIONPROTO:
        return source.parent
    else:
        return get_calling_function(source.parent)

def check_diagnostics(diagnostics):
    '''check diagnostics,
    if exists, print to stdout and return True
    '''
    has_diagnostics = False
    for dia in diagnostics:
        has_diagnostics = True
        print dia
    return has_diagnostics

def get_declaration_cursor(cursor):
    '''get declaration cursor of input cursor
    '''
    assert(isinstance(cursor, Cursor))
    return _conf.lib.clang_getCursorReferenced(cursor)

def get_semantic_parent_of_decla_cursor(cursor):
    '''get semantic_parent of declaration cursor
    '''
    assert(isinstance(cursor, Cursor))
    decla_cursor = get_declaration_cursor(cursor)
    if not isinstance(decla_cursor, Cursor) or \
            decla_cursor.semantic_parent is None:
        return None
    return decla_cursor.semantic_parent

