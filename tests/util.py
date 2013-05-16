''' utility functions for unit tests. '''

from clang.cindex import  TranslationUnit
from reshaper.ast import TUCache

def get_tu_from_text(source):
    '''just for unit test
    '''
    name = 't.cpp'
    args = []
    args.append('-std=c++11')

    return TUCache(TranslationUnit.from_source(name, args, 
                                               unsaved_files=[(name,
                                                              source)]), name)
        


