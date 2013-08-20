'''
Created on Jul 11, 2013

@author: liangzhao
'''
import reshaper.semantic as sem
import os


def get_source_for_header(header_path):
    for source in sem.get_source_path_candidates(header_path):
        if os.path.isfile(source):
            return os.path.abspath(source)
        
    return ''

def get_callee_cls_files(cls_cursor, keep_func = lambda c: True):
    ''' get source/header file of all callee classes,
        use keep_func to filter callees
    '''
    
    all_methods = sem.get_methods_from_class(cls_cursor)
    
    header_paths = set([])
        
    keep_func_new = lambda c: keep_func(c) and not sem.is_member_of(c, cls_cursor.spelling)  
       
    for method in all_methods:
        method_def = method.get_definition()
        if method_def is not None:
            transform_func = lambda c: os.path.abspath(c.location.file.name)
            _header_paths = set(sem.get_func_callees( \
                                      method_def, keep_func_new, transform_func).values())
            header_paths |= _header_paths
            
    header2source = {}
    
    for header in header_paths:
        header2source[header] = get_source_for_header(header) 
            
    return header2source     
   
def get_callee_cls_files_in_same_lib(cls_cursor):
    
    def is_in_same_lib(cursor):   
        caller_path = os.path.abspath(cursor.location.file.name)   
        callee_path = os.path.abspath(cls_cursor.location.file.name)
        
        caller_dir = os.path.dirname(caller_path)
        caller_header_path = os.path.abspath(os.path.join(caller_dir, '..'))
        callee_dir = os.path.dirname(callee_path)
        
        return callee_dir == callee_dir or caller_header_path == callee_dir
        
    return get_callee_cls_files(cls_cursor, is_in_same_lib)   
