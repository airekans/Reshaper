from reshaper import db
from clang.cindex import CursorKind as ckind
from clang.cindex import TypeKind as tkind
from nose.tools import eq_, with_setup, nottest
from .util import get_tu_from_text
from reshaper.ast import get_tu
import os


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
    

def with_param_setup(setup):
    """ util decorator to pass parameters to test functions
    """
    
    def decorate(func):
        
        def wrap_func():
            param_dict = setup()
            func(**param_dict) # test function returns nothing
        
        wrap_func.func_name = func.func_name
        return wrap_func
    
    return decorate

@nottest
def setup_for_test_file():
    TEST_INPUT = \
"""
int main()
{
    return 0;
}
"""

    _tu = get_tu_from_text(TEST_INPUT, 't.cpp')
    _proj_engine = db.ProjectEngine('test', is_in_memory = True)
    return {'tu': _tu, 'proj_engine': _proj_engine}

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
def setup_for_test_file_with_multiple_files():
    SOURCE_PATH = os.path.join(FILE_TEST_DIR, 'main.cpp')
    _tu = get_tu(SOURCE_PATH, is_from_cache_first=False)
    assert _tu
    _proj_engine = db.ProjectEngine('test', is_in_memory = True)
    return {'tu': _tu, 'proj_engine': _proj_engine}

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


@with_param_setup(setup_for_test_file)
def test_cursor_kind(tu, proj_engine):   
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
    
    for kind in ckind.get_all_kinds():
        db_ckind = db.CursorKind.from_clang_cursor_kind(kind, proj_engine)
        assert_ckind_equal(kind, db_ckind)

@with_param_setup(setup_for_test_file)
def test_type_kind(tu, proj_engine):
    def assert_tkind_equal(tkind, db_tkind):
        eq_(tkind.name, db_tkind.name)
        eq_(tkind.spelling, db_tkind.spelling)
    
    for kind in _get_clang_type_kinds():
        db_tkind = db.TypeKind.from_clang_type_kind(kind, proj_engine)
        assert_tkind_equal(kind, db_tkind)

@with_param_setup(setup_for_test_file)
def test_cursor(tu, proj_engine):
    pass

