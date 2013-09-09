"""util functions for semantic parsing
"""

import os

from clang.cindex import CursorKind
from clang.cindex import TypeKind
from reshaper import util 
from reshaper.util import is_cursor_in_file_func
from functools import partial

_file_types = ('.cpp', '.c', '.cc')




def is_cursor(source):
    return hasattr(source, "get_children")
        
def is_tu(source):
    return hasattr(source, "cursor")

def get_cursors_add_parent(source, spelling):
    '''Get Cursors through tu or cursor 
    according to its spelling and displayname
    '''
    children = []
    cursors = []
    if is_cursor(source):
        children = source.get_children()
    else:
        # Assume TU
        children = source.cursor.get_children()

    for cursor in children:
        if is_tu(source):
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
                                  c.semantic_parent.get_usr() == \
                                  class_cursor.get_usr()  and
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
    if not is_cursor(source) or \
            source.parent is None or \
            not is_cursor(source.parent):
        return None
    elif source.parent.type.kind == TypeKind.FUNCTIONPROTO:
        return source.parent
    else:
        return get_caller(source.parent)


def get_semantic_parent_of_decla_cursor(cursor):
    '''get semantic_parent of declaration cursor
    '''
    decla_cursor = util.get_declaration(cursor)
    if not is_cursor(decla_cursor) or \
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
    def get_underlying_type(cursor_type):
        '''recursively extract typedef type's underlying type
        '''
        if cursor_type.kind == TypeKind.TYPEDEF:
            result_type = cursor_type.get_declaration().underlying_typedef_type
            return get_underlying_type(result_type)
        else:
            return cursor_type
        
    if get_underlying_type(cursor.type).kind == TypeKind.POINTER:
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

def is_namespace(cursor):
    return cursor.kind == CursorKind.NAMESPACE

def is_namespace_definition(cursor, namespace_name = None):
    return cursor.is_definition() and is_namespace(cursor) and\
        namespace_name in [None, cursor.spelling, cursor.displayname]
        

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


def get_func_callees(fun_cursor, 
                     keep_func = lambda c: True, 
                     transform_func = lambda c: c):
    """get the callees of fun_cursor, which are memfunc type.
        
    Arguments:
    - `fun_cursor`: a function definition cursor
    - keep_func: used to filter child cursors,
    - transform_func: used to transform a result cursor 
    
    Return:
    all callee cursors in a dict with <hash, cursor> type
    
    """
    
    if fun_cursor is None or not fun_cursor.is_definition():
        return {} 

    # get all member function calls
    def is_member_fun_call(c):
        if c.kind != CursorKind.CALL_EXPR:
            return False
        
        decl_cur = util.get_declaration(c)

        return decl_cur.kind == CursorKind.CXX_METHOD or \
               decl_cur.kind == CursorKind.CONSTRUCTOR

        
    # get all member function calls in the function
    member_fun_calls = util.get_cursors_if(fun_cursor, is_member_fun_call)
    
    hash2decl_cursor = {}
    for c in member_fun_calls:
        decl_cursor = util.get_declaration(c) 
        if keep_func(decl_cursor):
            hash2decl_cursor[decl_cursor.hash] = transform_func(decl_cursor)
        
    return hash2decl_cursor


def is_member_of(cursor, callee_class_name):
    
    decl_sem_parent = get_semantic_parent_of_decla_cursor(cursor)
    if not decl_sem_parent:
        return False
    
    return decl_sem_parent.spelling == callee_class_name

def get_func_callee_names(fun_cursor, callee_class):
    """get the class callees of the function named fun_cursor.
    class callees means the class methods.
    
    Arguments:
    - `fun_cursor`: function cursor
    - `callee_class`: name of the class
    """
           
    keep_func = lambda c: is_member_of(c, callee_class)
                        
    transform_func = lambda c: c.spelling
                    
    hash2method_names = get_func_callees(fun_cursor, keep_func, transform_func)
    return set(hash2method_names.values())

def get_class_callee_names(cls_cursor, callee_class):
    """ get the names of class callees from the class given as cls_cursor.
    class callee means class methods.
    
    Arguments:
    - `cls_cursor`: cursor of the class calling the class callees
    - `callee_class`: the name of the used class
    """
    
    keep_func = lambda c: is_member_of(c, callee_class)
                        
    transform_func = lambda c: c.spelling
    
    func_names = get_class_callees(cls_cursor, keep_func, 
                                   transform_func)
        
    return set(func_names)

def get_class_callees(cls_cursor,  \
                      keep_func = lambda c: True, 
                      transform_func = lambda c: c):
    """ get the class callees' cursors from the class given as cls_cursor.
    class callee means class methods.
    keep_func is used to filter child cursors,
    transform_func is used to transform a result cursor 
    """
    all_methods = get_methods_from_class(cls_cursor)
    cursor_dict = {}
    
    keep_func_new = lambda c: keep_func(c) and not is_member_of(c, cls_cursor.spelling)  
       
    for method in all_methods:
        method_def = method.get_definition()
        if method_def is not None:
            used_methods = get_func_callees(method_def, keep_func_new, \
                                            transform_func)
            cursor_dict.update(used_methods)
        else:
            print "Cannot find definition of %s::%s" % \
                (cls_cursor.spelling, method.spelling)
        
    
    def compare_name(c1,c2):
        try:
            return cmp(c1.spelling, c2.spelling)    
        except:
            return cmp(c1, c2)
        
    return sorted(cursor_dict.values(), compare_name)

    

def is_header(fpath):
    return fpath.endswith( ('.h', '.hh', '.hpp') )

def is_source(fpah):
    return  

def get_source_path_candidates(fpath):
    dir_name, fname = os.path.split(fpath)
    fname_wo_surfix, _ = os.path.splitext(fname)
    
    sub_dir_candidates = ['', 'src']
    surfix_candidates = ['.cc', '.cpp', '.c']
    
    
    return [ os.path.join(dir_name, sub_dir, fname_wo_surfix+surfix) \
             for sub_dir in sub_dir_candidates \
             for surfix in surfix_candidates ]

def is_typeref(cursor):
    return cursor.kind == CursorKind.TYPE_REF

def get_class_definition(cursor):
    ''' given reference of a class, 
    find the initial definition which is not a typedef
    '''
    if not cursor:
        return None
    
    if is_class_definition(cursor):
        return cursor
    
    if is_typeref(cursor) or is_base_sepcifier(cursor):
        return get_class_definition(cursor.get_definition())
    
    if cursor.kind == CursorKind.TYPEDEF_DECL or \
           cursor.kind == CursorKind.FIELD_DECL :
        for c in cursor.get_children():
            definition = get_class_definition(c)
            if definition:
                return definition
            
    return None

def get_used_cls_names(cls_cursor):
    ''' get names of the  classes  used by func_cursor
    '''
      
    callees = get_class_callees(cls_cursor)
    
    hash2cursor = {}
    
    for callee in callees:
        callee_cls = get_semantic_parent_of_decla_cursor(callee)
        if callee_cls:
            hash2cursor[callee_cls.hash] = callee_cls
    
    return [cursor.spelling for cursor in hash2cursor.values()]


def is_cursor_in_dir(cursor, dir_path):
    ''' return True is cursor's file is in dir_path'''
    loc = cursor.location
    if not loc.file:
        return False
    file_path = os.path.abspath(loc.file.name)
    abs_dir = os.path.abspath(dir_path) + '/'
    return file_path.startswith(abs_dir)


def get_name(cursor):
    return cursor.spelling
    
def get_children_attrs(cursor, keep_func, 
                       attr_getter= get_name, is_sorted = False):
    assert(cursor is not None)
    
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

    
def get_class_cursor_in_file(source, class_name, file_path):
    ''' get class/struct cursor with class_name and file_path'''
    return util.get_cursor_if(source,
                              partial(is_class_name_matched, \
                                      class_name = class_name),
                              is_cursor_in_file_func(file_path))
         
     
def get_all_class_cursors(source, header_path = None):
    ''' get all cursors of class or struct type, defined in header_path'''
    
    if not header_path:
        is_visit_subtree_fun = lambda _c, _l : True
    else:
        is_visit_subtree_fun = is_cursor_in_file_func(header_path)
    
    return util.get_cursors_if(source, is_class, \
                                is_visit_subtree_fun)
 
def get_all_class_names(source, header_path):
    ''' get names of all class or struct type'''
    
    if not header_path:
        is_visit_subtree_fun = lambda _c, _l : True
    else:
        is_visit_subtree_fun = is_cursor_in_file_func(header_path)
    
    return util.get_cursors_if(source, is_class, \
                                is_visit_subtree_fun, \
                                transform_fun = get_name)

def get_classes_with_names(source, names):
    """ get classes with given names

    `names` : a list of class names
    """

    classes = get_all_class_cursors(source)
    return [cls for cls in classes if cls.spelling in names]
    
def get_member_var_classes(cls_cursor, keep_cls_func=lambda c: True):
    
    assert(is_class(cls_cursor))
    
    member_var_cursors = get_children_attrs(cls_cursor, 
                                            is_non_static_var, 
                                            attr_getter=lambda c: c)
    member_with_def_classes = []
    for member_var in member_var_cursors:
        cls_def_cursor = get_class_definition(member_var)
        if cls_def_cursor and keep_cls_func(cls_def_cursor):
            member_with_def_classes.append((member_var, \
                                       cls_def_cursor))
    return member_with_def_classes


def is_base_sepcifier(cursor):
    return cursor.kind == CursorKind.CXX_BASE_SPECIFIER

def get_base_cls_cursors(cls_cursor):
    return util.get_cursors_if(cls_cursor, is_base_sepcifier,
                          transform_fun = get_class_definition)

