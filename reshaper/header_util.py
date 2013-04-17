'''
utility module to get various info from a header file
'''
from clang.cindex import  CursorKind, TypeKind
from reshaper import util
from functools import partial
from reshaper.util import is_curor_in_file_func

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

def get_name(cursor):
    return cursor.spelling
    
def get_children_attrs(cursor, keep_func, 
                       attr_getter= get_name, is_sorted = False):
    if not cursor:
        return []
    
    mb_var_attrs = []
    for child in cursor.get_children():
        if keep_func is None or keep_func(child):
            mb_var_attrs.append(attr_getter(child))
        else:
            continue  # for debug purpose
    if is_sorted:
        return sorted(mb_var_attrs)
    else: 
        return mb_var_attrs
    
def get_non_static_var_names(cursor):
    ''' get names of non-static members''' 
    return get_children_attrs(cursor, is_non_static_var) 


def get_non_static_nonpt_var_names(cursor):  
    '''get names of all member variables \
    of non-pointer type from a class cursor'''
    keep_func = lambda c: is_non_static_var(c) and not is_pointer(c)
    return get_children_attrs(cursor, keep_func)
   

def get_non_static_pt_var_names(cursor):
    '''get names of all pointers type member variables\
    from a class cursor
    '''
    keep_func = lambda c: is_non_static_var(c) and is_pointer(c)
    return get_children_attrs(cursor, keep_func)


def is_class(cursor):
    ''' is class or struct definition cursor'''
    return cursor.kind == CursorKind.CLASS_DECL or \
            cursor.kind == CursorKind.STRUCT_DECL

def is_class_name_matched(cursor, _class_name):
    return cursor.spelling == _class_name and \
           is_class(cursor)


    
def get_class_cursor(source, _class_name, header_path):
    ''' get class/struct cursor with _class_name and header_path'''
    return util.get_cursor_if(source,
                               partial(is_class_name_matched, \
                                       _class_name = _class_name),
                               is_curor_in_file_func(header_path))
 		
 	
def get_all_class_cursors(source):
    ''' get all cursors of class or struct type'''
    return util.get_cursors_if(source, is_class)
 
def get_all_class_names(source, header_path):
    ''' get names of all class or struct type'''
    return util.get_cursors_if(source, is_class, \
                                is_curor_in_file_func(header_path), \
                                transform_fun = get_name)

