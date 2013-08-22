''' utility functions for unit tests. '''

from clang.cindex import  TranslationUnit
from reshaper.ast import TUCache

import sys, os

def get_tu_from_text(source):
    '''just for unit test
    '''
    name = 't.cpp'
    args = []
    args.append('-std=c++11')

    return TUCache(TranslationUnit.from_source(name, args, 
                                               unsaved_files=[(name,
                                                              source)]), name)
        
class RedirectStdStreams(object):
    '''redirect stderr to remove error message during test
    '''
    def __init__(self, stderr=open(os.devnull, 'w')):
        self._stderr = stderr or sys.stderr

    def __enter__(self):
        self.old_stderr = sys.stderr
        self.old_stderr.flush()
        sys.stderr = self._stderr

    def __exit__(self, exc_type, exc_value, traceback):
        self._stderr.flush()
        sys.stderr = self.old_stderr
        
def RedirectStderr(func):
    '''redirect stderr function decorator
    '''
    def test_wrappedFunc():
        with RedirectStdStreams():
            func()
    return test_wrappedFunc
