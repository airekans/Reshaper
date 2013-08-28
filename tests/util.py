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
        
def redirect_stderr(func):
    '''redirect stderr function decorator
    '''
    def test_wrapped_func():
        with RedirectStdStreams():
            func()
    return test_wrapped_func


def assert_stdout (expected_str):
    '''assert stdout string is expected string
    '''
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

def abnormal_exit(func):
    '''assert abnormal sys.exit is called
    '''
    def test_wrap(*arg, **kw):
        try:
            func(*arg, **kw)
        except SystemExit, e:
            assert(e.code != 0)
        except:
            raise
        else:
            message = "%s() did not raise abnormal SystemExit" \
            % (func.__name__)
            raise AssertionError(message)
    return test_wrap
        
        