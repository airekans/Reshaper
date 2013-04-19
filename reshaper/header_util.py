'''
utility module to get various info from a header file
'''
from reshaper import util
from functools import partial
from reshaper.util import is_curor_in_file_func
import reshaper.semantic as sem





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
    return get_children_attrs(cursor, sem.is_non_static_var) 


def get_non_static_nonpt_var_names(cursor):  
    '''get names of all member variables \
    of non-pointer type from a class cursor'''
    keep_func = lambda c: sem.is_non_static_var(c) and not sem.is_pointer(c)
    return get_children_attrs(cursor, keep_func)
   

def get_non_static_pt_var_names(cursor):
    '''get names of all pointers type member variables\
    from a class cursor
    '''
    keep_func = lambda c: sem.is_non_static_var(c) and sem.is_pointer(c)
    return get_children_attrs(cursor, keep_func)

    
def get_class_cursor(source, _class_name, header_path):
    ''' get class/struct cursor with _class_name and header_path'''
    return util.get_cursor_if(source,
                               partial(sem.is_class_name_matched, \
                                       _class_name = _class_name),
                               is_curor_in_file_func(header_path))
 		
 	
def get_all_class_cursors(source):
    ''' get all cursors of class or struct type'''
    return util.get_cursors_if(source, sem.is_class)
 
def get_all_class_names(source, header_path):
    ''' get names of all class or struct type'''
    return util.get_cursors_if(source, sem.is_class, \
                                is_curor_in_file_func(header_path), \
                                transform_fun = get_name)

