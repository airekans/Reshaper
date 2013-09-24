'''test functions in remove_invalid_includes.py
'''

import os
from clang.cindex import CursorKind
from nose.tools import eq_
from remove_invalid_includes import IncludeHandler, get_used_include_file 
from functools import partial
from tests.util import redirect_stderr

INPUT_DIR = os.path.join(os.path.dirname(__file__), 'test_data')

def test_class_IncludeHandler():
    source_file = os.path.join(INPUT_DIR, "use_all.cpp")
    include_obj = IncludeHandler(source_file)
    includes = include_obj.get_header_list()
    eq_(len(includes), 4)

    useful_includes = include_obj.get_useful_includes()
    eq_(len(useful_includes), 5)

    useless_includes = include_obj.get_invalid_includes()
    eq_(len(useless_includes), 0)

def test_class_IncludeHandler_failed():
    source_file = os.path.join(INPUT_DIR, "use_partial.cpp")
    include_obj = IncludeHandler(source_file)
    includes = include_obj.get_header_list()
    eq_(len(includes), 4)

    useful_includes = include_obj.get_useful_includes()
    eq_(len(useful_includes), 3)

    useless_includes = include_obj.get_invalid_includes()
    eq_(len(useless_includes), 2)

@redirect_stderr
def test_remove_invalid_includes_for_file():
    source_file = os.path.join(INPUT_DIR, "use_partial.cpp")
    include_obj = IncludeHandler(source_file)
    includes = include_obj.get_header_list()
    eq_(len(includes), 4)

    get_used_include_file(source_file, None, "~/.reshaper.cfg", False)

    clean_file = os.path.join(INPUT_DIR, "use_partial.cpp.header.bak")
    clean_include_obj = IncludeHandler(clean_file)
    includes_clean = clean_include_obj.get_header_list()
    eq_(len(includes_clean), 2)

