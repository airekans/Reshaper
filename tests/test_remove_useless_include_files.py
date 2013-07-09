'''test functions in remove_useless_include_files.py
'''

import os
from clang.cindex import CursorKind
from nose.tools import eq_
from reshaper.ast import get_tu
from reshaper.util import get_cursor_if
from remove_useless_include_files import get_useful_include_file, \
        get_useless_include_list, remove_useless_includes
from functools import partial

INPUT_DIR = os.path.join(os.path.dirname(__file__), 'test_data')

def test_get_useful_include_file():
    """test get_useful_include_file
    """

    def is_macro_instance_cursor(cursor, cursor_kind, name, line):
        """called by get_cursor_if to get cursor
        """
        if cursor is None or cursor.location is None:
            return False
        if cursor.kind == cursor_kind and \
                cursor.displayname == name and cursor.location.line == line:
            return True
        return False

    source_file = os.path.join(INPUT_DIR, "use_all.cpp")
    source_tu = get_tu(source_file, options=1)
    useful_file_list = []

    define_cursor = get_cursor_if(source_tu, partial(is_macro_instance_cursor, \
            cursor_kind = CursorKind.MACRO_INSTANTIATION, name = "HEADER_ONE_STRING", line=10))
    get_useful_include_file(define_cursor, 0, useful_file_list)
    eq_(len(useful_file_list), 1)
    assert("typedef.h" in useful_file_list[0])

    macro_cursor = get_cursor_if(source_tu, partial(is_macro_instance_cursor, \
            cursor_kind = CursorKind.MACRO_INSTANTIATION, name = "Max", line=14))
    get_useful_include_file(macro_cursor, 0, useful_file_list)
    eq_(len(useful_file_list), 2)
    assert("macro.h" in useful_file_list[1])

def test_get_useless_include_list():
    """test to get useless include files list
    """
    source_file = os.path.join(INPUT_DIR, "use_all.cpp")
    useless_include_list = get_useless_include_list(source_file, None, None)
    eq_(len(useless_include_list), 0)

    macro_file = os.path.join(INPUT_DIR, "use_macro.cpp")
    macro_useless_include_list = get_useless_include_list(macro_file, None, None)
    eq_(len(macro_useless_include_list), 3)

    files_str = ""
    for f in macro_useless_include_list:
        files_str += f
    assert("typedef.h" in files_str)
    assert("static_func.h" in files_str)
    assert("enum_header.h" in files_str)

def test_remove_useless_includes():
    """test remove_useless_includes
    """
    source_file = os.path.join(INPUT_DIR, "use_macro.cpp")
    include_list = []
    ret_with_none = remove_useless_includes(source_file, include_list)
    assert(not ret_with_none)

    useless_include_list = get_useless_include_list(source_file, None, None)
    eq_(len(useless_include_list), 3)
    ret_tmp_file = remove_useless_includes(source_file, useless_include_list)
    assert(os.path.isfile(ret_tmp_file))

    new_file_useless_includes = get_useless_include_list(ret_tmp_file, None, None)
    eq_(len(new_file_useless_includes), 0)

