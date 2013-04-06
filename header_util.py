'''
utility module to get various info from a header file
'''
from clang.cindex import Index, CursorKind, TypeKind

def parse(header_path):
    index = Index.create()
    tu = index.parse(header_path, args=['-x', 'c++', '-std=c++11'])
    if not tu:
        raise Exception('Cannot open header file %s' % header_path)
    return tu




def is_smart_ptr(cursor):
    smart_ptrs = set("shared_ptr auto_ptr \
                      weak_ptr scoped_ptr shard_array scoped_array".split())
    
    for child in cursor.get_children():    
        if child.displayname in smart_ptrs:
            return True
        
    return False

def is_pt_type(cursor):
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
    



    
def non_static_var_names(cursor):
    return get_children_attrs(cursor, is_non_static_var) 

def non_static_nonpt_var_names(cursor):  
    '''get names of all member variables \
    of non-pointer type from a class cursor'''
    keep_func = lambda c: is_non_static_var(c) and not is_pt_type(c)
    return get_children_attrs(cursor, keep_func)
   

def non_static_pt_var_names(cursor):
    '''get names of all pointers type member variables\
    from a class cursor
    '''
    keep_func = lambda c: is_non_static_var(c) and is_pt_type(c)
    return get_children_attrs(cursor, keep_func)



def match_class_name(cursor, class_name):
    return cursor.spelling == class_name and \
            (cursor.kind == CursorKind.CLASS_DECL or \
             cursor.kind == CursorKind.STRUCT_DECL)


    
def get_class_decl_cursor(cursor, class_name):
    if(match_class_name(cursor, class_name)):
        return cursor
    else:
        for child in cursor.get_children():
            cursor = get_class_decl_cursor(child, class_name)
            if cursor:
                return cursor
        return None
 		
 	
 
 


