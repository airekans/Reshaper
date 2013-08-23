''' utility functions for unit tests. '''

from clang.cindex import  TranslationUnit
from reshaper.ast import TUCache

import sys, os, StringIO

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


def AssertStdout (expected_str):
    def outer_wrap(func):
        def test_inner_wrap():
            saved_stdout = sys.stdout
            try:
                out = StringIO.StringIO()
                sys.stdout = out
                func()
                output = out.getvalue().strip()
                assert output == expected_str
            finally:
                sys.stdout = saved_stdout
        return test_inner_wrap
    return outer_wrap
            
