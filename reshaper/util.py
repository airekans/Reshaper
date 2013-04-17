# This file provides common utility functions for the test suite.

from clang.cindex import Cursor
from clang.cindex import CursorKind
from clang.cindex import TranslationUnit
import ConfigParser
import os
from functools import partial
from reshaper.semantic import get_semantic_parent_of_decla_cursor

def get_tu(source,all_warnings=False, config_path = '~/.reshaper.cfg'):
    """Obtain a translation unit from source and language.

    By default, the translation unit is created from source file "t.<ext>"
    where <ext> is the default file extension for the specified language. By
    default it is C, so "t.c" is the default file name.

    all_warnings is a convenience argument to enable all compiler warnings.
    """
    args = ['-x', 'c++', '-std=c++11']
 
    if all_warnings:
        args += ['-Wall', '-Wextra']

    if config_path:
        config_parser = ConfigParser.SafeConfigParser()
        config_parser.read(['.reshaper.cfg', os.path.expanduser(config_path)])
        if config_parser.has_option('Clang Options', 'include_paths'):
            include_paths = config_parser.get('Clang Options', 'include_paths')
            # pylint: disable-msg=E1103
            args += ['-I' + p for p in include_paths.split(',')]
            
        if config_parser.has_option('Clang Options', 'include_files'):
            include_files = config_parser.get('Clang Options', 'include_files')
            # pylint: disable-msg=E1103
            for ifile in include_files.split(','):
                args += ['-include', ifile]
        
    #print ' '.join(args)

    return TranslationUnit.from_source(source, args)

def get_cursor(source, spelling):
    """Obtain a cursor from a source object.

    This provides a convenient search mechanism to find a cursor with specific
    spelling within a source. The first argument can be either a
    TranslationUnit or Cursor instance.

    If the cursor is not found, None is returned.
    """

    return get_cursor_if(source, lambda c: c.spelling == spelling)

def get_cursor_if(source, is_satisfied_fun, is_visit_subtree_fun = lambda _x, _y: True):
    """Obtain a cursor from a source object by a predicate function f.
    If f(cursor) returns True, then the cursor is return.
    If no cursor is found, returns None.
    
    Arguments:
    - `source`: Cursor or TranslationUnit
    - `is_satisfied_fun`: predicate function used to check whether the
        cursor is the one we want.
        function signature is bool is_satisfied_fun(cursor)
    """

    is_get_result = [False]
    def visit(cursor):
        if is_satisfied_fun(cursor):
            is_get_result[0] = True
            return True
        else:
            return False

    cursors = get_cursors_if(source, visit,
                             lambda _c, _l: not is_get_result[0] and 
                                            is_visit_subtree_fun(_c,_l))

    return cursors[0] if len(cursors) > 0 else None
    
    
def get_cursors(source, spelling):
    """Obtain all cursors from a source object with a specific spelling.

    This provides a convenient search mechanism to find all cursors with specific
    spelling within a source. The first argument can be either a
    TranslationUnit or Cursor instance.

    If no cursors are found, an empty list is returned.
    """

    return get_cursors_if(source, lambda c: c.spelling == spelling)
    
def get_cursors_if(source, is_satisfied_fun,
                   is_visit_subtree_fun = lambda _x, _y: True,
                   transform_fun = lambda c: c):
    """ Get cursors satisfying function f from cursor c.
    If no cursors are found, an empty list is returned.
    
    Arguments:
    - `source`: 
    - `is_satisfied_fun`: predicate function user gives
    - `is_visit_subtree_fun`:
    - `transform_fun`:
    """

    cursors = []

    def visit(cursor, _):
        if is_satisfied_fun(cursor):
            cursors.append(transform_fun(cursor))

    walk_ast(source, visit, is_visit_subtree_fun)

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


def is_same_file(path1, path2):
    return os.path.abspath(path1) == \
           os.path.abspath(path2) 

def is_curor_in_file_func(file_path):
    def is_curor_in_file(cursor, _l):
        cursor_file = cursor.location.file
        if not cursor_file:
            return  True
        else:
            return is_same_file(cursor_file.name, file_path)
    
    return is_curor_in_file

def walk_ast(source, visitor, is_visit_subtree_fun = lambda _c, _l: True):
    """walk the ast with the specified functions by DFS
    
    Arguments:
    - `source`: 
    - `visitor`: function used to visit the cursor
         the function signature: visitor(cursor, level)
    - `is_visit_subtree_fun`: function used to determind whether
         we want to visit the subtree rooted at cursor.
         the function signature: bool is_visit_subtree_fun(cursor, level)
    """

    if source is None:
        return
    elif isinstance(source, Cursor):
        cursor = source
    else: 
        # Assume TU
        cursor = source.cursor

    def walk_ast_with_level(cursor, level):
        if not is_visit_subtree_fun(cursor, level):
            return
            
        visitor(cursor, level)

        child_level = level + 1
        for c in cursor.get_children():
            walk_ast_with_level(c, child_level)

    walk_ast_with_level(cursor, 0)

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

