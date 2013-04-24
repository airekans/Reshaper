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


def get_methods_from_class(class_cursor, methods = None):
    """ get selected methods from a given class cursor.
    If methods is None is not specified,
    then all methods will be returned.
    
    Arguments:
    - `class_cursor`: given class cursor 
    - `methods`: method names
    """
    method_set = set(methods) if methods is not None else None
    member_method_cursors = \
        util.get_cursors_if(class_cursor,
                            lambda c: (c.kind == CursorKind.CXX_METHOD and
                                  (c.spelling in method_set
                                   if method_set is not None else True)))
    return member_method_cursors

    
def scan_dir_parse_files(directory, parse_file):
    '''Scan directory recursivly to 
    get files with file_types
    '''
    for root, _, files in os.walk(directory):
        for file_name in files:
            _, file_type = os.path.splitext(file_name)
            if file_type in _file_types:
                parse_file(os.path.join(root, file_name))

def get_caller(source):
    '''get calling function of source cursor
    '''
    if not isinstance(source, Cursor) or \
            source.parent is None or \
            not isinstance(source.parent, Cursor):
        return None
    elif source.parent.type.kind == TypeKind.FUNCTIONPROTO:
        return source.parent
    else:
        return get_caller(source.parent)

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

def is_class_name_matched(cursor, class_name):
    return cursor.spelling == class_name and \
           is_class(cursor)

def is_class_definition(cursor, class_name = None):
    """ Check whether the cursor is the definition of
    class named class_name.
    If class_name is not given, check whether the cursor
    is a class difinition.
    
    Arguments:
    - `cursor`: the class cursor to be checked
    - `class_name`: the name of the class
    """
    if class_name is not None:
        return is_class_name_matched(cursor, class_name) and \
            cursor.is_definition()
    else:
        return is_class(cursor) and cursor.is_definition()


def is_function(cursor):
    """ check whether the cursor is a function.
    A function is either a C function or a method of a class.
    
    Arguments:
    - `cursor`: function cursor
    """
    return cursor.type.kind == TypeKind.FUNCTIONPROTO

def is_function_name_matched(cursor, fun_name):
    """ Check whether the cursor is a function named fun_name
    
    Arguments:
    - `cursor`: function cursor
    - `fun_name`: the name of the function
    """
    return is_function(cursor) and \
        cursor.spelling == fun_name
    
def is_function_definition(cursor, fun_name = None):
    """ Check whether the cursor is the definition of
    function named fun_name.
    If fun_name is not given, check whether the cursor is
    a function definition.
    
    Arguments:
    - `cursor`: function cursor
    - `fun_name`: function name
    """
    if fun_name is not None:
        return is_function_name_matched(cursor, fun_name) and \
            cursor.is_definition()
    else:
        return is_function(cursor) and cursor.is_definition()
    
           
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

def get_func_callees(fun_cursor, used_class):
    """get the usage of the class from the function given as fun_cursor.
    
    Arguments:
    - `fun_cursor`: function cursor
    - `used_class`: name of the used class
    """
    if fun_cursor is None or not fun_cursor.is_definition():
        return set()

    # get all member function calls
    def is_member_fun_call(c):
        if c.kind != CursorKind.CALL_EXPR:
            return False

        for child in c.get_children():
            return child.kind == CursorKind.MEMBER_REF_EXPR

        return False
        
    # get all member function calls in the function
    member_fun_calls = util.get_cursors_if(fun_cursor, is_member_fun_call)
    
    target_member_fun_calls = \
        [c for c in member_fun_calls
         if get_semantic_parent_of_decla_cursor(c).spelling == used_class]
    target_member_funs = \
        [get_declaration_cursor(c) for c in target_member_fun_calls]
    method_names = [c.spelling for c in target_member_funs]
    return set(method_names)

def get_class_callees(cls_cursor, used_class):
    """ get the usage of used_class from the class given as cls_cursor
    
    Arguments:
    - `cls_cursor`: cursor of the class using used_class
    - `used_class`: the name of the used class
    """
    all_methods = get_methods_from_class(cls_cursor)

    method_names = set()
    for method in all_methods:
        method_def = method.get_definition()
        if method_def is not None:
            used_methods = get_func_callees(method_def, used_class)
            method_names = method_names.union(used_methods)
        else:
            print "Cannot find definition of %s::%s" % \
                (used_class, method.spelling)
        
    return method_names

