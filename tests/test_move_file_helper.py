'''
test move_file_helper.py
'''
import os
from nose.tools import eq_
from reshaper.ast import get_tu
from move_file_helper import MoveFileHandle

INPUT_DIR = os.path.join(os.path.dirname(__file__), 'test_data')

def test_MoveFileHandle():
    '''test if MoveFileHandle can work rightly
    '''
    source_file = os.path.join(INPUT_DIR, "move_file_helper_test.cpp")
    file_obj = MoveFileHandle(get_tu, source_file, '', 3)

    source_tu = get_tu(source_file)
    file_obj.begin_to_handle_for_UT(source_tu)
    includes = file_obj.get_output_list()

    eq_(3, len(includes))

    assert('move_file_helper_test.h' in includes[0].file_name)
    eq_(1, includes[0].depth)

    assert('no_source_header.h' in includes[1].file_name)
    eq_(1, includes[1].depth)

    assert('indirectly_include.h' in includes[2].file_name)
    eq_(2, includes[2].depth)

def test_get_includes_for_source_file():
    '''test get includes for source file
    '''
    source_file = os.path.join(INPUT_DIR, "move_file_helper_test.cpp")
    file_obj = MoveFileHandle(get_tu, source_file, '', 3)

    source_includes = []
    includes, _ = file_obj.get_includes_for_source_file('', \
            source_file)
    eq_(2, len(includes))
    assert('move_file_helper_test.h' in includes[0])
    assert('no_source_header.h' in includes[1])

def test_get_includes_for_header_file():
    '''test get includes for header file without source file
    '''
    header_file = os.path.join(INPUT_DIR, "no_source_header.h")
    header_name = os.path.abspath(header_file)

    source_file = os.path.join(INPUT_DIR, "move_file_helper_test.cpp")
    source_tu = get_tu(source_file)

    file_obj = MoveFileHandle(get_tu, source_file, '', 3)
    includes = file_obj.get_includes_for_header_file(header_name, \
            source_tu.get_includes())
    eq_(1, len(includes))
    assert('indirectly_include.h' in includes[0])

