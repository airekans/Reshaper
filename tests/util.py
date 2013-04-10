''' utility functions for unit tests. '''

from clang.cindex import  TranslationUnit


def get_tu_from_text(source):
    '''copy it from util.py, 
    just for test
    '''
    name = 't.cpp'
    args = ['-x', 'c++', '-std=c++11']

    return TranslationUnit.from_source(name, args,
                                       unsaved_files=[(name, source)])

