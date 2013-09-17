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
    if not isinstance(expected, set):
        expected = set(expected)
    if not isinstance(actual, set):
        actual = set(actual)
        
    eq_(expected, actual, msg)

