from reshaper import db
from clang.cindex import CursorKind as ckind
from clang.cindex import TypeKind as tkind
from nose.tools import eq_, with_setup
from .util import get_tu_from_text
from reshaper.ast import get_tu
import os


_TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')

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
    expected_all_tkinds = [tkind.from_id(_i) for _i in xrange(30)]
    expected_all_tkinds += [tkind.from_id(_i) for _i in xrange(100, 114)]
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
    actual_file_names = set(file.name for file in
                            proj_engine.get_session().query(db.File).all())
    eq_(expected_file_names, actual_file_names)

    # Test file with include
    INPUT_FILE = os.path.join(_TEST_DATA_DIR, 'class.cpp')
    _tu = get_tu(INPUT_FILE, is_from_cache_first = False)
    proj_engine.build_db_file(_tu)
    expected_file_names = \
        set(['t.cpp', os.path.join(_TEST_DATA_DIR, 'class.h'),
             os.path.join(_TEST_DATA_DIR, 'class.cpp')])
    actual_file_names = set(file.name for file in
                            proj_engine.get_session().query(db.File).all())
    eq_(expected_file_names, actual_file_names)
    

_tu = None
_proj_engine = None

def setup_for_test_file():
    global _tu, _proj_engine

    TEST_INPUT = \
"""
int main()
{
    return 0;
}
"""

    _tu = get_tu_from_text(TEST_INPUT, 't.cpp')
    _proj_engine = db.ProjectEngine('test', is_in_memory = True)
    
@with_setup(setup_for_test_file)
def test_file_get_pending_filenames():
    pending_files = db.File.get_pending_filenames(_tu, _proj_engine)
    eq_(set(['t.cpp']), pending_files)

    _proj_engine.build_db_file(_tu)
    pending_files = db.File.get_pending_filenames(_tu, _proj_engine)
    assert not pending_files

@with_setup(setup_for_test_file)
def test_file_from_clang_tu():
    expected_file = _tu.get_file(_tu.spelling)
    file = db.File.from_clang_tu(_tu, _tu.spelling, _proj_engine)
    eq_(expected_file.name, file.name)
    eq_(expected_file.time, file.time)

@with_setup(setup_for_test_file)
def test_cursor_kind():   
    def assert_ckind_equal(ckind, db_ckind):
        eq_(ckind.name, db_ckind.name)
        return False
    
    for kind in ckind.get_all_kinds():
        db_ckind = db.CursorKind.from_clang_cursor_kind(kind, _proj_engine)
        assert_ckind_equal(kind, db_ckind)

