'''
utility module to get various info from a header file
'''
from clang.cindex import  CursorKind, TypeKind
from reshaper import util
from functools import partial

SMART_PTRS = set(["shared_ptr", "auto_ptr","weak_ptr",\
                  "scoped_ptr","shard_array","scoped_array"])

def is_smart_ptr(cursor):
    f = lambda c: c.displayname in SMART_PTRS
    smart_ptr_cursor = util.get_cursor_if(cursor, f)  
    return (smart_ptr_cursor is not None)
    
def is_pointer(cursor):
    if cursor.type.kind == TypeKind.POINTER:
        return True
    
    return is_smart_ptr(cursor)
    
def is_non_static_var(cursor):
    return cursor.kind == CursorKind.FIELD_DECL

def get_name(cursor):
    return cursor.spelling
    
def get_children_attrs(cursor, keep_func, 
                       attr_getter= get_name, is_sorted = True):
    mb_var_names = []
    for child in cursor.get_children():
        if keep_func is None or keep_func(child):
            mb_var_names.append(attr_getter(child))
        else:
            continue  # for debug purpose
    if is_sorted:
        return sorted(mb_var_names)
    else: 
        return mb_var_names
    



    
def get_non_static_var_names(cursor):
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



def is_class_name_matched(cursor, class_name):
    return cursor.spelling == class_name and \
            (cursor.kind == CursorKind.CLASS_DECL or \
             cursor.kind == CursorKind.STRUCT_DECL)


    
def get_class_decl_cursor(source, class_name):
    return util.get_cursor_if(source,
                               partial(is_class_name_matched, class_name = class_name))
 		
 	
 
 


