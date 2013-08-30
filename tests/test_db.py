from reshaper import db
from clang.cindex import CursorKind as ckind
from clang.cindex import TypeKind as tkind
import clang.cindex as cindex
from nose.tools import eq_, with_setup, nottest
from .util import get_tu_from_text
from reshaper.ast import get_tu
from reshaper.util import get_cursor, get_cursor_if
import os
from functools import partial
from _xmlplus.xpath.XPathParser import PARENT


_TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')

def _get_clang_type_kinds():
    all_tkinds = [tkind.from_id(_i) for _i in xrange(30)]
    all_tkinds += [tkind.from_id(_i) for _i in xrange(100, 114)]
    return all_tkinds

def test_project_engine_initialize():
    """ Project Engine will initialize DB in its ctor. Test this behavior.
    """

    proj_engine = db.ProjectEngine('test', is_in_memory = True)
    assert proj_engine.get_session() is not None
    
    # After initialization, there should be CursorKind and TypeKind in DB.
    expected_all_ckinds = ckind.get_all_kinds()
    actual_all_ckinds = proj_engine.get_session().query(db.CursorKind).all()
    eq_(len(expected_all_ckinds), len(actual_all_ckinds))

    expected_ckind_names = set(kind.name for kind in expected_all_ckinds)
    actual_ckind_names = set(kind.name for kind in actual_all_ckinds)
    eq_(expected_ckind_names, actual_ckind_names)

    # Check TypeKind
    expected_all_tkinds = _get_clang_type_kinds()
    actual_all_tkinds = proj_engine.get_session().query(db.TypeKind).all()
    eq_(len(expected_all_tkinds), len(actual_all_tkinds))

    expected_tkind_names = set(kind.name for kind in expected_all_tkinds)
    actual_tkind_names = set(kind.name for kind in actual_all_tkinds)
    eq_(expected_tkind_names, actual_tkind_names)

def test_project_engine_build_file():
    TEST_INPUT = \
"""
int main()
{
    return 0;
}
"""
    _tu = get_tu_from_text(TEST_INPUT, 't.cpp')
    proj_engine = db.ProjectEngine('test', is_in_memory = True)
    assert proj_engine.get_session() is not None

    proj_engine.build_db_file(_tu)

    expected_file_names = set(['t.cpp'])
    actual_file_names = set(_file.name for _file in
                            proj_engine.get_session().query(db.File).all())
    eq_(expected_file_names, actual_file_names)

    # Test file with include
    INPUT_FILE = os.path.join(_TEST_DATA_DIR, 'class.cpp')
    _tu = get_tu(INPUT_FILE, is_from_cache_first = False)
    proj_engine.build_db_file(_tu)
    expected_file_names = \
        set(['t.cpp', os.path.join(_TEST_DATA_DIR, 'class.h'),
             os.path.join(_TEST_DATA_DIR, 'class.cpp')])
    actual_file_names = set(_file.name for _file in
                            proj_engine.get_session().query(db.File).all())
    eq_(expected_file_names, actual_file_names)
    

def with_param_setup(setup, *args, **kw_args):
    """ util decorator to pass parameters to test functions
    """
    
    def decorate(func):
        
        def wrap_func():
            param_dict = setup(*args, **kw_args)
            func(**param_dict) # test function returns nothing
        
        wrap_func.func_name = func.func_name
        return wrap_func
    
    return decorate


@nottest
def setup_for_memory_file(source):
    _tu = get_tu_from_text(source, 't.cpp')
    _proj_engine = db.ProjectEngine('test', is_in_memory = True)
    return {'tu': _tu, 'proj_engine': _proj_engine}

@nottest
def setup_for_test_file():
    TEST_INPUT = \
"""
int main()
{
    return 0;
}
"""

    return setup_for_memory_file(TEST_INPUT)

@with_param_setup(setup_for_test_file)
def test_file_get_pending_filenames(tu, proj_engine):
    pending_files = db.File.get_pending_filenames(tu, proj_engine)
    eq_(set(['t.cpp']), pending_files)

    proj_engine.build_db_file(tu)
    pending_files = db.File.get_pending_filenames(tu, proj_engine)
    assert not pending_files

@with_param_setup(setup_for_test_file)
def test_file_from_clang_tu(tu, proj_engine):
    expected_file = tu.get_file(tu.spelling)
    _file = db.File.from_clang_tu(tu, tu.spelling, proj_engine)
    eq_(expected_file.name, _file.name)
    eq_(expected_file.time, _file.time)


FILE_TEST_DIR = os.path.join(_TEST_DATA_DIR, 'db', 'file')

@nottest
def setup_for_fs_file(_file):
    _tu = get_tu(_file, is_from_cache_first=False)
    assert _tu
    _proj_engine = db.ProjectEngine('test', is_in_memory = True)
    return {'tu': _tu, 'proj_engine': _proj_engine}

@nottest
def setup_for_test_file_with_multiple_files():
    SOURCE_PATH = os.path.join(FILE_TEST_DIR, 'main.cpp')
    return setup_for_fs_file(SOURCE_PATH)


@with_param_setup(setup_for_test_file_with_multiple_files)
def test_file_get_pending_filenames_with_multiple_files(tu, proj_engine):
    pending_files = db.File.get_pending_filenames(tu, proj_engine)
    expected_files = set(os.path.join(FILE_TEST_DIR, _file) 
                         for _file in ['main.cpp', 'c.h', 'b.h', 'a.h'] )
    eq_(expected_files, pending_files)
    
    proj_engine.build_db_file(tu)
    pending_files = db.File.get_pending_filenames(tu, proj_engine)
    assert not pending_files
    db_files = proj_engine.get_session().query(db.File).all()
    actual_file_names = set(_file.name for _file in db_files)
    eq_(expected_files, actual_file_names)
    
    # check file inclusion
    expected_includes = {'main.cpp': set(['b.h', 'c.h']),
                         'b.h': set(['a.h']),
                         'c.h': set(),
                         'a.h': set()}
    eq_(len(expected_includes), len(actual_file_names))
    for _file in db_files:
        file_name = os.path.basename(_file.name)
        assert file_name in expected_includes, _file.name
        eq_(expected_includes[file_name], 
            set([os.path.basename(included.name)
                 for included in _file.includes]))
    
    # get the new tu for c.h
    c_tu = get_tu(os.path.join(FILE_TEST_DIR, 'c.h'), is_from_cache_first=False)
    pending_files = db.File.get_pending_filenames(c_tu, proj_engine)
    assert not pending_files


def assert_ckind_equal(ckind, db_ckind):
    eq_(ckind.name, db_ckind.name)
    eq_(ckind.is_declaration(), db_ckind.is_declaration)
    eq_(ckind.is_reference(), db_ckind.is_reference)
    eq_(ckind.is_expression(), db_ckind.is_expression)
    eq_(ckind.is_statement(), db_ckind.is_statement)
    eq_(ckind.is_attribute(), db_ckind.is_attribute)
    eq_(ckind.is_translation_unit(), db_ckind.is_translation_unit)
    eq_(ckind.is_preprocessing(), db_ckind.is_preprocessing)
    eq_(ckind.is_unexposed(), db_ckind.is_unexposed)

@with_param_setup(setup_for_test_file)
def test_cursor_kind(tu, proj_engine):
    for kind in ckind.get_all_kinds():
        db_ckind = db.CursorKind.from_clang_cursor_kind(kind, proj_engine)
        assert_ckind_equal(kind, db_ckind)


def assert_tkind_equal(tkind, db_tkind):
    eq_(tkind.name, db_tkind.name)
    eq_(tkind.spelling, db_tkind.spelling)

@with_param_setup(setup_for_test_file)
def test_type_kind(tu, proj_engine):
    for kind in _get_clang_type_kinds():
        db_tkind = db.TypeKind.from_clang_type_kind(kind, proj_engine)
        assert_tkind_equal(kind, db_tkind)


TEST_CURSOR_INPUT = """
class A
{
    int data;
};
"""

def assert_cursor_equal(cursor, db_cursor):
    eq_(cursor.spelling, db_cursor.spelling)
    eq_(cursor.displayname, db_cursor.displayname)
    eq_(cursor.get_usr(), db_cursor.usr)
    eq_(cursor.is_definition(), db_cursor.is_definition)
    eq_(db_cursor.location_start, cursor.location)
    eq_(db_cursor.location_end, cursor.extent.end)
    assert_ckind_equal(cursor.kind, db_cursor.kind)

@with_param_setup(setup_for_memory_file, TEST_CURSOR_INPUT)
def test_cursor_ctor(tu, proj_engine):
    A_cursor = get_cursor(tu, 'A')
    db_A_cursor = db.Cursor(A_cursor, proj_engine)
    
    assert_cursor_equal(A_cursor, db_A_cursor)


def is_in_db(cursor, proj_engine):
    return len(proj_engine.get_session().query(db.Cursor).\
               filter(db.Cursor.usr == cursor.get_usr()).all()) > 0

@with_param_setup(setup_for_memory_file, TEST_CURSOR_INPUT)
def test_cursor_from_clang_cursor_with_new_cursor(tu, proj_engine):
    # ensure that this cursor is not in DB
    A_cursor = get_cursor(tu, 'A')
    assert not is_in_db(A_cursor, proj_engine)
    
    db_A_cursor = db.Cursor.from_clang_cursor(A_cursor, proj_engine)
    
    # check if this cursor is in DB.
    assert_cursor_equal(A_cursor, db_A_cursor)


def fake_build_db_cursor(cursor, proj_engine):
    
    def build_db_cursor(cursor, parent, left):
        db_cursor = db.Cursor(cursor, proj_engine)
        db_cursor.parent = parent
        db_cursor.left = left
        
        proj_engine.get_session().add(db_cursor)
        
        child_left = left + 1
        if cursor.kind != cindex.CursorKind.TEMPLATE_TEMPLATE_PARAMETER:
            for child in cursor.get_children():
                child_left = build_db_cursor(child, db_cursor, child_left) + 1
        
        right = child_left
        db_cursor.right = right
    
        proj_engine.get_session().add(db_cursor)
        proj_engine.get_session().commit()
        proj_engine.get_session().expire(db_cursor)
    
        return right

    left = 0
    if cursor.kind == cindex.CursorKind.TRANSLATION_UNIT:
        for child in cursor.get_children():
            if child.location.file:
                left = build_db_cursor(child, None, left) + 1
    else:
        build_db_cursor(cursor, None, left)

@with_param_setup(setup_for_memory_file, TEST_CURSOR_INPUT)
def test_cursor_from_clang_cursor_with_db_cursor(tu, proj_engine):
    A_cursor = get_cursor(tu, 'A')
    fake_build_db_cursor(A_cursor, proj_engine)
    # ensure that the cursor is in db
    assert is_in_db(A_cursor, proj_engine)
    
    db_A_cursor = db.Cursor.from_clang_cursor(A_cursor, proj_engine)
    
    assert_cursor_equal(A_cursor, db_A_cursor)

TEST_CURSOR_MACRO_INPUT = """
#define DECL_AND_DEFINE(name) \
class name; \
class name \
{}

DECL_AND_DEFINE(Test);

Test t;

"""

@with_param_setup(setup_for_memory_file, TEST_CURSOR_MACRO_INPUT)
def test_cursor_from_clang_cursor_with_tmpl_cursor(tu, proj_engine):
    Test_decl_cursor = get_cursor_if(tu, lambda c: c.spelling == 'Test' and \
                                            not c.is_definition())
    Test_def_cursor = get_cursor_if(tu, lambda c: c.spelling == 'Test' and \
                                            c.is_definition())
    assert not is_in_db(Test_decl_cursor, proj_engine)
    assert not is_in_db(Test_def_cursor, proj_engine)

    db_Test_decl_cursor = db.Cursor.from_clang_cursor(Test_decl_cursor,
                                                      proj_engine)
    assert_cursor_equal(Test_decl_cursor, db_Test_decl_cursor)
    
    fake_build_db_cursor(tu.cursor, proj_engine)
    # get from db
    db_Test_decl_cursor = db.Cursor.from_clang_cursor(Test_decl_cursor,
                                                      proj_engine)
    assert_cursor_equal(Test_decl_cursor, db_Test_decl_cursor)
    
    db_Test_def_cursor = db.Cursor.from_clang_cursor(Test_def_cursor,
                                                     proj_engine)
    assert_cursor_equal(Test_def_cursor, db_Test_def_cursor)


CURSOR_TEST_DIR = os.path.join(_TEST_DATA_DIR, 'db', 'cursor')

@with_param_setup(setup_for_fs_file, os.path.join(CURSOR_TEST_DIR, 'a.cpp'))
def test_cursor_from_clang_cursor_with_same_spelling(tu, proj_engine):
    pass
    
