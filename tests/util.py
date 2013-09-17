''' utility functions for unit tests. '''

from clang.cindex import  TranslationUnit
from nose.tools import eq_

def get_tu_from_text(source, filename = "t.cpp"):
    '''just for unit test
    '''
    name = filename or 't.cpp'
    args = []
    args.append('-std=c++11')

    return TranslationUnit.from_source(name, args, 
                                       unsaved_files=[(name, source)])
        
def set_eq(expected, actual, msg = None):
    ''' asserts that set expected is equal to set actual.
    '''
    if not isinstance(expected, set):
        expected = set(expected)
    if not isinstance(actual, set):
        actual = set(actual)
        
    eq_(expected, actual, msg)



def with_param_setup(setup, *args, **kw_args):
    """ util decorator to pass parameters to test functions
    """
    
    def decorate(func):
        
        def wrap_func():
            params = setup(*args, **kw_args)
            if isinstance(params, dict):
                func(**params) # test function returns nothing
            elif isinstance(params, (list, tuple)):
                func(*params)
            else:
                func(params) # fall back
        
        wrap_func.func_name = func.func_name
        return wrap_func
    
    return decorate
