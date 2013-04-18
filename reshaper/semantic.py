"""util functions for semantic parsing
"""

import os
from clang.cindex import Cursor
from clang.cindex import CursorKind
from clang.cindex import TranslationUnit
from clang.cindex import TypeKind
from clang.cindex import Config
from reshaper import util 

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
        if isinstance(source, TranslationUnit):
            cursor.parent = None
        else:
            cursor.parent = source

        if cursor.is_definition():
            if cursor.spelling == spelling:
                cursors.append(cursor)
        elif spelling in cursor.displayname :
            cursors.append(cursor)
        # Recurse into children.
        cursors.extend( get_cursors_add_parent(cursor, spelling))
    return cursors

def scan_dir_parse_files(directory, parse_file):
    '''Scan directory recursivly to 
    get files with file_types
    '''
    for root, _, files in os.walk(directory):
        for file_name in files:
            _, file_type = os.path.splitext(file_name)
            if file_type in _file_types:
                parse_file(os.path.join(root, file_name))

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
    return _conf.lib.clang_getCursorReferenced(cursor)

def get_semantic_parent_of_decla_cursor(cursor):
    '''get semantic_parent of declaration cursor
    '''
    decla_cursor = get_declaration_cursor(cursor)
    if not isinstance(decla_cursor, Cursor) or \
            decla_cursor.semantic_parent is None:
        return None
    return decla_cursor.semantic_parent


_SMART_PTRS = set(["shared_ptr", "auto_ptr", "weak_ptr", \
             "scoped_ptr", "shard_array", "scoped_array"])

def is_smart_ptr(cursor):
    ''' is smart pointer type '''
    f = lambda c: c.displayname in _SMART_PTRS
    smart_ptr_cursor = util.get_cursor_if(cursor, f)  
    return (smart_ptr_cursor is not None)
    
def is_pointer(cursor):
    ''' is pointer type '''
    if cursor.type.kind == TypeKind.POINTER:
        return True
    
    return is_smart_ptr(cursor)
    
def is_non_static_var(cursor):
    ''' is non-static member var'''
    return cursor.kind == CursorKind.FIELD_DECL

def is_class(cursor):
    ''' is class or struct definition cursor'''
    return cursor.kind == CursorKind.CLASS_DECL or \
            cursor.kind == CursorKind.STRUCT_DECL

def is_class_name_matched(cursor, _class_name):
    return cursor.spelling == _class_name and \
           is_class(cursor)
           
           
def get_full_qualified_name(cursor):
    '''use to get semantic_parent.spelling :: cursor.spelling or displayname 
    infomation of the input cursors;
    for example: TestUSR::test_decla(int), MyNameSpace::test_defin(double)
    or test_function(TestUSR&)
    '''
    seman_parent = get_semantic_parent_of_decla_cursor(cursor)
    out_str = cursor.displayname
    if out_str == None:
        out_str = cursor.spelling

    if seman_parent is not None and \
            (seman_parent.kind == CursorKind.NAMESPACE or\
            seman_parent.kind == CursorKind.CLASS_DECL):
        return "%s::%s" % (seman_parent.spelling, out_str)
    else:
        return out_str

           
           

