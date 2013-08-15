from reshaper import db
from clang.cindex import CursorKind as ckind
from clang.cindex import TypeKind as tkind
from nose.tools import eq_


def test_project_engine_initialize():
    """
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
    

def test_file():
    pass

    