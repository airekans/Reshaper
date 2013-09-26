from reshaper import db
from clang.cindex import CursorKind as ckind
from clang.cindex import TypeKind as tkind
import clang.cindex as cindex
from nose.tools import eq_, nottest
from .util import get_tu_from_text
from reshaper.ast import get_tu
from reshaper.util import get_cursor, get_cursor_if, get_cursors_if
import os
from sqlalchemy.sql import func
from tests.util import set_eq, with_param_setup


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
    _tu = get_tu(INPUT_FILE)
    proj_engine.build_db_file(_tu)
    expected_file_names = \
        set(['t.cpp', os.path.join(_TEST_DATA_DIR, 'class.h'),
             os.path.join(_TEST_DATA_DIR, 'class.cpp')])
    actual_file_names = set(_file.name for _file in
                            proj_engine.get_session().query(db.File).all())
    eq_(expected_file_names, actual_file_names)
    

@nottest
def setup_for_memory_file(source):
    _tu = get_tu_from_text(source, 't.cpp')
    _proj_engine = db.ProjectEngine('test', is_in_memory = True)
    return _tu, _proj_engine

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


FILE_TEST_DIR = os.path.join(_TEST_DATA_DIR, 'db', 'file')

@nottest
def setup_for_fs_file(_file):
    _tu = get_tu(_file)
    assert _tu
    _proj_engine = db.ProjectEngine('test', is_in_memory = True)
    return _tu, _proj_engine

@nottest
def setup_for_test_file_with_multiple_files():
    SOURCE_PATH = os.path.join(FILE_TEST_DIR, 'main.cpp')
    return setup_for_fs_file(SOURCE_PATH)



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


def is_db_file(_file):
    return _file.id is not None

@with_param_setup(setup_for_test_file_with_multiple_files)
def test_file_from_clang_tu_with_includes(tu, proj_engine):
    _file = db.File.from_clang_tu(tu, tu.spelling, proj_engine)
    proj_engine.get_session().commit()
    
    assert is_db_file(_file)
    
    expected_files = set([inc.source.name for inc in tu.get_includes()])
    expected_files = \
        expected_files.union(set([inc.include.name for inc in tu.get_includes()]))
    
    actual_files = proj_engine.get_session().query(db.File).all()
    eq_(expected_files, set([_f.name for _f in actual_files]))


@with_param_setup(setup_for_test_file_with_multiple_files)
def test_file_get_pending_filenames_with_multiple_files(tu, proj_engine):
    pending_files = db.File.get_pending_filenames(tu, proj_engine)
    expected_files = set(os.path.join(FILE_TEST_DIR, _file) 
                         for _file in ['main.cpp', 'c.h', 'b.h', 'a.h'])
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
    c_tu = get_tu(os.path.join(FILE_TEST_DIR, 'c.h'))
    pending_files = db.File.get_pending_filenames(c_tu, proj_engine)
    assert not pending_files

def test_file_get_pending_filenames_with_multiple_files_2():
    ''' tests get_pending_filenames with the ".." cases
    test1/test1.cpp and test2/test2.cpp both reference a.h by using -I.. option
    This will cause clang returns the "test1/../a.h" and "test2/../a.h".
    But they are actually the same file.
    '''
    TEST1_DIR = os.path.join(FILE_TEST_DIR, 'test1')
    TEST2_DIR = os.path.join(FILE_TEST_DIR, 'test2')
    TEST1_PATH = os.path.join(TEST1_DIR, 'test1.cpp')
    TEST2_PATH = os.path.join(TEST2_DIR, 'test2.cpp')
    
    test1_tu = get_tu(TEST1_PATH, args=['-I', os.path.join(TEST1_DIR, '..')])
    test2_tu = get_tu(TEST2_PATH, args=['-I', os.path.join(TEST2_DIR, '..')])
    proj_engine = db.ProjectEngine('test', is_in_memory = True)
    
    pending_files = db.File.get_pending_filenames(test1_tu, proj_engine)
    expected_files = set([os.path.join(FILE_TEST_DIR, 'a.h'), TEST1_PATH])
    eq_(expected_files, pending_files)
    
    proj_engine.build_db_file(test1_tu)
    
    all_db_files = proj_engine.get_session().query(db.File).all()
    set_eq(expected_files, [_f.name for _f in all_db_files])
    
    pending_files = db.File.get_pending_filenames(test2_tu, proj_engine)
    expected_files = set([TEST2_PATH])
    eq_(expected_files, pending_files)


def assert_ckind_equal(_ckind, db_ckind):
    eq_(_ckind.name, db_ckind.name)
    eq_(_ckind.is_declaration(), db_ckind.is_declaration)
    eq_(_ckind.is_reference(), db_ckind.is_reference)
    eq_(_ckind.is_expression(), db_ckind.is_expression)
    eq_(_ckind.is_statement(), db_ckind.is_statement)
    eq_(_ckind.is_attribute(), db_ckind.is_attribute)
    eq_(_ckind.is_translation_unit(), db_ckind.is_translation_unit)
    eq_(_ckind.is_preprocessing(), db_ckind.is_preprocessing)
    eq_(_ckind.is_unexposed(), db_ckind.is_unexposed)

@with_param_setup(setup_for_test_file)
def test_cursor_kind(tu, proj_engine):
    for kind in ckind.get_all_kinds():
        db_ckind = db.CursorKind.from_clang_cursor_kind(kind, proj_engine)
        assert_ckind_equal(kind, db_ckind)


def assert_tkind_equal(_tkind, db_tkind):
    eq_(_tkind.name, db_tkind.name)
    eq_(_tkind.spelling, db_tkind.spelling)

@with_param_setup(setup_for_test_file)
def test_type_kind(_, proj_engine):
    for kind in _get_clang_type_kinds():
        db_tkind = db.TypeKind.from_clang_type_kind(kind, proj_engine)
        assert_tkind_equal(kind, db_tkind)


TEST_CURSOR_INPUT = """
class A
{
    int data;
    void foo();
};

void A::foo()
{}
"""

def assert_cursor_equal(cursor, db_cursor):
    eq_(cursor.spelling, db_cursor.spelling)
    eq_(cursor.displayname, db_cursor.displayname)
    eq_(cursor.get_usr(), db_cursor.usr)
    eq_(cursor.is_definition(), db_cursor.is_definition)
    eq_(db_cursor.location_start, cursor.location)
    eq_(db_cursor.location_end, cursor.extent.end)
    assert_ckind_equal(cursor.kind, db_cursor.kind)
    
    if cursor.lexical_parent is not None and \
        cursor.lexical_parent.kind != ckind.TRANSLATION_UNIT:
        assert_cursor_equal(cursor.lexical_parent, db_cursor.lexical_parent)
        
    if cursor.semantic_parent is not None and \
        cursor.semantic_parent.kind != ckind.TRANSLATION_UNIT:
        assert_cursor_equal(cursor.semantic_parent, db_cursor.semantic_parent)

@with_param_setup(setup_for_memory_file, TEST_CURSOR_INPUT)
def test_cursor_ctor(tu, proj_engine):
    A_cursor = get_cursor(tu, 'A')
    db_A_cursor = db.Cursor(A_cursor, proj_engine)
    
    assert_cursor_equal(A_cursor, db_A_cursor)
    
    # test lexical_parent
    data_cursor = get_cursor(tu, 'data')
    db_data_cursor = db.Cursor(data_cursor, proj_engine)
    assert_cursor_equal(data_cursor, db_data_cursor)
    
    # test semantic_parent
    foo_cursor = get_cursor(tu, 'foo')
    db_foo_cursor = db.Cursor(foo_cursor, proj_engine)
    assert_cursor_equal(foo_cursor, db_foo_cursor)
    
    foo_cursor = get_cursor_if(tu, lambda c: c.spelling == 'foo' and
                                        c.is_definition())
    db_foo_cursor = db.Cursor(foo_cursor, proj_engine)
    assert_cursor_equal(foo_cursor, db_foo_cursor)

def is_in_db(cursor, proj_engine):
    return len(proj_engine.get_session().query(db.Cursor).\
               filter(db.Cursor.usr == cursor.get_usr()).all()) > 0

def is_db_cursor(db_cursor):
    return db_cursor.id is not None

@with_param_setup(setup_for_memory_file, TEST_CURSOR_INPUT)
def test_cursor_from_clang_cursor_with_new_cursor(tu, proj_engine):
    # ensure that this cursor is not in DB
    for spelling in ['A', 'data', 'foo']:
        _cursor = get_cursor(tu, spelling)
        assert not is_in_db(_cursor, proj_engine)
        
        db_cursor = db.Cursor.from_clang_cursor(_cursor, proj_engine)
        
        # check if this cursor is in DB.
        assert not is_db_cursor(db_cursor)
        assert_cursor_equal(_cursor, db_cursor)


def fake_build_db_cursor(cursor, proj_engine):
    
    def build_db_cursor(cursor, parent, left):
        db_cursor = db.Cursor.from_clang_cursor(cursor, proj_engine)
        db_cursor.parent = parent
        db_cursor.left = left
        
        refer_cursor = cursor.referenced
        if refer_cursor is not None and \
           refer_cursor.location.file is not None and \
           (refer_cursor.location.file.name != cursor.location.file.name or \
            refer_cursor.location.offset != cursor.location.offset) and \
           refer_cursor.kind != ckind.TRANSLATION_UNIT:
            db_cursor.referenced = \
                db.Cursor.from_clang_referenced(refer_cursor, proj_engine)
            proj_engine.get_session().add(db_cursor.referenced)
        
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
    fake_build_db_cursor(tu.cursor, proj_engine)
    for spelling in ['A', 'data', 'foo']:
        _cursor = get_cursor(tu, spelling)

        # ensure that the cursor is in db
        assert is_in_db(_cursor, proj_engine)
        
        db_cursor = db.Cursor.from_clang_cursor(_cursor, proj_engine)
        
        assert is_db_cursor(db_cursor)
        assert_cursor_equal(_cursor, db_cursor)


TEST_CURSOR_MACRO_INPUT = """
#define DECL_AND_DEFINE(name) \
class name; \
class name \
{ \
public: \
    int data; \
}

DECL_AND_DEFINE(Test);

int main()
{
    Test t;
    t;
    return 0;
}
"""

@with_param_setup(setup_for_memory_file, TEST_CURSOR_MACRO_INPUT)
def test_cursor_from_clang_cursor_with_decl_cursor(tu, proj_engine):
    Test_decl_cursor = get_cursor_if(tu, lambda c: c.spelling == 'Test' and \
                                            not c.is_definition())
    Test_def_cursor = get_cursor_if(tu, lambda c: c.spelling == 'Test' and \
                                            c.is_definition())
    assert not is_in_db(Test_decl_cursor, proj_engine)
    assert not is_in_db(Test_def_cursor, proj_engine)

    db_Test_decl_cursor = db.Cursor.from_clang_cursor(Test_decl_cursor,
                                                      proj_engine)
    assert not is_db_cursor(db_Test_decl_cursor)
    assert_cursor_equal(Test_decl_cursor, db_Test_decl_cursor)
    
    fake_build_db_cursor(tu.cursor, proj_engine)
    # get from db
    db_Test_decl_cursor = db.Cursor.from_clang_cursor(Test_decl_cursor,
                                                      proj_engine)
    assert is_db_cursor(db_Test_decl_cursor)
    assert_cursor_equal(Test_decl_cursor, db_Test_decl_cursor)
    
    db_Test_def_cursor = db.Cursor.from_clang_cursor(Test_def_cursor,
                                                     proj_engine)
    assert is_db_cursor(db_Test_def_cursor)
    assert_cursor_equal(Test_def_cursor, db_Test_def_cursor)

@with_param_setup(setup_for_memory_file, TEST_CURSOR_MACRO_INPUT)
def test_cursor_from_clang_cursor_with_non_def_cursor(tu, proj_engine):
    t_cursor = get_cursor_if(tu, lambda c: not c.spelling and
                                    c.displayname == 't')
    assert t_cursor
    assert not is_in_db(t_cursor, proj_engine)
    
    db_t_cursor = db.Cursor.from_clang_cursor(t_cursor, proj_engine)
    assert not is_db_cursor(db_t_cursor)
    assert_cursor_equal(t_cursor, db_t_cursor)
    
    # build the whole AST into db
    fake_build_db_cursor(tu.cursor, proj_engine)

    db_t_cursor = db.Cursor.from_clang_cursor(t_cursor, proj_engine)
    assert not is_db_cursor(db_t_cursor)
    assert_cursor_equal(t_cursor, db_t_cursor)


TEST_NAMESPACE_INPUT = '''
namespace out_ns {
namespace ns {
class A;
void foo(const A&); // this line will cause problem
}
}

namespace out_ns {
namespace ns {
class A
{
    int data;
};
}
}
'''

@with_param_setup(setup_for_memory_file, TEST_NAMESPACE_INPUT)
def test_cursor_from_clang_cursor_with_same_lex_sem_parent(tu, proj_engine):
    fake_build_db_cursor(tu.cursor, proj_engine)
    
    db_ns_cursors = proj_engine.get_session().query(db.Cursor).\
        filter(db.Cursor.spelling == 'ns').all()
    eq_(2, len(db_ns_cursors))


CURSOR_TEST_DIR = os.path.join(_TEST_DATA_DIR, 'db', 'cursor')

@with_param_setup(setup_for_fs_file, os.path.join(CURSOR_TEST_DIR, 'a.cpp'))
def test_cursor_from_clang_cursor_with_same_spelling(tu, proj_engine):
    cursors = get_cursors_if(tu, lambda c: c.spelling == 'A' and
                                    c.is_definition())
    eq_(2, len(cursors))
    
    fake_build_db_cursor(tu.cursor, proj_engine)

    for cursor in cursors:
        db_cursor = db.Cursor.from_clang_cursor(cursor, proj_engine)
        assert is_db_cursor(db_cursor)
        assert_cursor_equal(cursor, db_cursor)


TEST_CURSOR_DEF_INPUT = '''
class A;
class A;
namespace ns {
class B;
}

void foo();

class A
{};

namespace ns {
class B
{};
}

void foo()
{}
'''

def verify_db_def_cursor(spelling, expected_decl_len, tu, proj_engine):
    def_cursor = get_cursor_if(tu, lambda c: c.spelling == spelling and
                                    c.is_definition())
    assert is_in_db(def_cursor, proj_engine)
    
    db_def_cursor = db.Cursor.from_clang_cursor(def_cursor, proj_engine)
    assert is_db_cursor(db_def_cursor)
    
    db_decl_cursors = proj_engine.get_session().query(db.Cursor).\
        filter(db.Cursor.usr == def_cursor.get_usr()).\
        filter(db.Cursor.is_definition == False).all()
    eq_(expected_decl_len, len(db_decl_cursors))
    
    # verify that the cursor in DB does not have definition linked to it
    for db_cur in db_decl_cursors:
        assert is_db_cursor(db_cur)
        assert not db_cur.definition
    
    db.Cursor.update_declarations(db_def_cursor, proj_engine)
    
    # verify the cursor in DB has definition
    db_decl_cursors = proj_engine.get_session().query(db.Cursor).\
        filter(db.Cursor.usr == def_cursor.get_usr()).\
        filter(db.Cursor.is_definition == False).all()
    eq_(expected_decl_len, len(db_decl_cursors))
    for db_cur in db_decl_cursors:
        assert is_db_cursor(db_cur)
        assert db_cur.definition
        eq_(db_def_cursor, db_cur.definition)

@with_param_setup(setup_for_memory_file, TEST_CURSOR_DEF_INPUT)
def test_cursor_update_declarations(tu, proj_engine):
    fake_build_db_cursor(tu.cursor, proj_engine)
    
    verify_db_def_cursor('A', 2, tu, proj_engine)
    verify_db_def_cursor('B', 1, tu, proj_engine)
    verify_db_def_cursor('foo', 1, tu, proj_engine)

@with_param_setup(setup_for_memory_file, TEST_CURSOR_DEF_INPUT)
def test_cursor_get_definition_without_def(tu, proj_engine):
    A_def_cursor = get_cursor_if(tu, lambda c: c.spelling == 'A' and
                                        c.is_definition())
    assert not is_in_db(A_def_cursor, proj_engine)
    
    assert db.Cursor.get_definition(A_def_cursor, proj_engine) is None
    
    # build only declaration into db
    A_decl_cursor = get_cursor_if(tu, lambda c: c.spelling == 'A' and
                                        not c.is_definition())
    fake_build_db_cursor(A_decl_cursor, proj_engine)
    assert db.Cursor.get_definition(A_def_cursor, proj_engine) is None

@with_param_setup(setup_for_memory_file, TEST_CURSOR_DEF_INPUT)
def test_cursor_get_definition_with_def(tu, proj_engine):
    A_def_cursor = get_cursor_if(tu, lambda c: c.spelling == 'A' and
                                        c.is_definition())
    assert not is_in_db(A_def_cursor, proj_engine)
    
    assert db.Cursor.get_definition(A_def_cursor, proj_engine) is None
    
    # build decl and def into db
    fake_build_db_cursor(tu.cursor, proj_engine)
    expected_cursor = proj_engine.get_session().query(db.Cursor).\
        filter(db.Cursor.usr == A_def_cursor.get_usr()).\
        filter(db.Cursor.is_definition == True).one()
    eq_(expected_cursor, db.Cursor.get_definition(A_def_cursor, proj_engine))


TEST_CURSOR_REF_INPUT = '''
class A;
class A {};
int main()
{
    A a;
    a;
    return 0;
}
'''

@with_param_setup(setup_for_memory_file, TEST_CURSOR_REF_INPUT)
def test_cursor_from_referenced(tu, proj_engine):
    a_cursor = get_cursor_if(tu, lambda c: c.displayname == 'a' and
                                    c.kind == cindex.CursorKind.DECL_REF_EXPR)
    a_ref_cursor = a_cursor.referenced
    assert a_ref_cursor
    assert not is_in_db(a_cursor, proj_engine)
    
    db_a_cursor = db.Cursor.from_clang_referenced(a_ref_cursor, proj_engine)
    assert not is_db_cursor(db_a_cursor)
    
    fake_build_db_cursor(tu.cursor, proj_engine)
    db_a_cursor = db.Cursor.from_clang_referenced(a_ref_cursor, proj_engine)
    assert is_db_cursor(db_a_cursor)


TEST_CURSOR_REF_INPUT2 = '''
namespace ns {
template<typename T>
void foo(T t)
{}
}

namespace ns2 {
template<typename T>
void bar(T t)
{
    ns::foo(t);
}
}
'''

@with_param_setup(setup_for_memory_file, TEST_CURSOR_REF_INPUT2)
def test_cursor_from_referenced_without_spelling(tu, proj_engine):
    foo_call_cursor = \
        get_cursor_if(tu, lambda c: c.location.line == 12 and
                             c.kind == cindex.CursorKind.DECL_REF_EXPR)
    foo_ref_cursor = foo_call_cursor.referenced
    assert foo_ref_cursor
    assert foo_ref_cursor.spelling is None
    assert not is_in_db(foo_call_cursor, proj_engine)
    
    db_a_cursor = db.Cursor.from_clang_referenced(foo_ref_cursor, proj_engine)
    assert not is_db_cursor(db_a_cursor)
    
    fake_build_db_cursor(tu.cursor, proj_engine)
    db_a_cursor = db.Cursor.from_clang_referenced(foo_ref_cursor, proj_engine)
    assert is_db_cursor(db_a_cursor)

@with_param_setup(setup_for_memory_file, TEST_CURSOR_REF_INPUT)
def test_cursor_get_max_nested_set_index(tu, proj_engine):
    eq_(0, db.Cursor.get_max_nested_set_index(proj_engine))

    fake_build_db_cursor(tu.cursor, proj_engine)
    expected_max = proj_engine.get_session().\
            query(func.max(db.Cursor.right)).scalar()
    assert expected_max
    eq_(expected_max, db.Cursor.get_max_nested_set_index(proj_engine))

@with_param_setup(setup_for_memory_file, TEST_CURSOR_REF_INPUT)
def test_type_is_valid_type(tu, _):
    assert not db.Type.is_valid_clang_type(None)
    fake_type = lambda: True
    fake_type.kind = cindex.TypeKind.INVALID
    assert not db.Type.is_valid_clang_type(fake_type)
    
    A_cursor = get_cursor(tu, 'A')
    A_type = A_cursor.type
    assert A_type
    assert db.Type.is_valid_clang_type(A_type)


def is_db_type(_type):
    return _type.id is not None

TEST_TYPE_INPUT = '''
class A {};

A a;
A* ap;
A *ap2;
A*** app;
'''


def verify_type(tu, proj_engine, spelling, is_db):
    _cursor = get_cursor(tu, spelling)
    _type = _cursor.type
    assert _type
    db_type = db.Type.from_clang_type(_type, proj_engine)
    if is_db:
        assert is_db_type(db_type)
        while db_type.kind.name == 'POINTER':
            db_type = db_type.pointee
            assert is_db_type(db_type)
    else:
        assert not is_db_type(db_type)
        while db_type.kind.name == 'POINTER':
            db_type = db_type.pointee
            assert not is_db_type(db_type)

@with_param_setup(setup_for_memory_file, TEST_TYPE_INPUT)
def test_type_from_clang_type(tu, proj_engine):
    verify_type(tu, proj_engine, 'a', False)
    verify_type(tu, proj_engine, 'ap', False)
    verify_type(tu, proj_engine, 'ap2', False)
    verify_type(tu, proj_engine, 'app', False)
    
    # build the types into DB
    # we ignore ap2 here because its type is the same as ap
    for spelling in ['a', 'ap', 'app']:
        _cursor = get_cursor(tu, spelling)
        _type = _cursor.type
        assert _type
        db_type = db.Type.from_clang_type(_type, proj_engine)
        proj_engine.get_session().add(db_type)
    
    verify_type(tu, proj_engine, 'a', True)
    verify_type(tu, proj_engine, 'ap', True)
    verify_type(tu, proj_engine, 'ap2', True)
    verify_type(tu, proj_engine, 'app', True)

def simple_build_db_cursor(cursor, proj_engine):
    left = 0
    if cursor.kind == ckind.TRANSLATION_UNIT:
        for child in cursor.get_children():
            if child.location.file:
                left = proj_engine.build_db_cursor(child, None, left) + 1
    else:
        proj_engine.build_db_cursor(cursor, None, left)
    
    proj_engine.get_session().commit()

def assert_db_states(proj_engine, cursor_num, type_num):
    db_cursors = \
        proj_engine.get_session().query(db.Cursor).all()
    eq_(cursor_num, len(db_cursors))

    db_types = proj_engine.get_session().query(db.Type).all()
    eq_(type_num, len(db_types))
    
    return db_cursors, db_types

@with_param_setup(setup_for_memory_file, 'int a;')
def test_proj_engine_build_db_cursor_with_simple_stmt(tu, proj_engine):
    ''' Test builtin type declaration 
    '''
    
    simple_build_db_cursor(tu.cursor, proj_engine)
    
    db_cursors, db_types = assert_db_states(proj_engine, 1, 1)

    # verify the relations
    a_cursor = get_cursor(tu, 'a')
    db_a_cursor = db_cursors[0]
    assert_cursor_equal(a_cursor, db_a_cursor)
    assert db_a_cursor.type
    eq_(db_types[0], db_a_cursor.type)
    eq_('int', db_a_cursor.type.spelling)
    # because int is a buitin type, its declaration is None in DB.
    assert db_a_cursor.type.declaration is None


def assert_cursor_type(cursor, proj_engine):
    db_cursor = db.Cursor.get_db_cursor(cursor, proj_engine)
    assert db_cursor
    assert is_db_cursor(db_cursor)
    if cursor.type and cursor.type.kind != tkind.INVALID:
        eq_(cursor.type.spelling, db_cursor.type.spelling)
        assert_tkind_equal(cursor.type.kind, db_cursor.type.kind)
        decl = cursor.type.get_declaration()
        if decl and decl.kind != ckind.NO_DECL_FOUND:
            assert_cursor_equal(decl, db_cursor.type.declaration)
        else:
            assert db_cursor.type.declaration is None
    else:
        assert db_cursor.type is None
    
    for child in cursor.get_children():
        assert_cursor_type(child, proj_engine)

@with_param_setup(setup_for_memory_file, 'class A{}; A a;')
def test_proj_engine_build_db_cursor_with_simple_stmt_2(tu, proj_engine):
    ''' Test simple type definition and variable definition.
    '''
    
    simple_build_db_cursor(tu.cursor, proj_engine)
    
    db_cursors, db_types = assert_db_states(proj_engine, 5, 1)

    set_eq(['CLASS_DECL', 'VAR_DECL', 'TYPE_REF', 'CALL_EXPR', 'CONSTRUCTOR'],
           [c.kind.name for c in db_cursors])
    
    # verify declaration of the type
    A_def_cursor = proj_engine.get_session().\
        query(db.Cursor).join(db.CursorKind).\
        filter(db.Cursor.spelling == 'A').\
        filter(db.CursorKind.name == 'CLASS_DECL').\
        filter(db.Cursor.is_definition == True).one()
    assert A_def_cursor
    A_type = db_types[0]
    assert A_type
    eq_(A_def_cursor, A_type.declaration)
    
    # verify the type of the cursor
    for _c in tu.cursor.get_children():
        if _c.location.file: # skip builtin cursors
            assert_cursor_type(_c, proj_engine)


TEST_BUILD_DB_CURSOR_INPUT_1 = '''
struct B {};

struct A
{
    B data;
};

void foo()
{
    A a;
    a.data;
}
'''

@with_param_setup(setup_for_memory_file, TEST_BUILD_DB_CURSOR_INPUT_1)
def test_proj_engine_build_db_cursor_with_simple_stmt_3(tu, proj_engine):
    ''' Test more complex type definition and variable definition.
    '''
    
    simple_build_db_cursor(tu.cursor, proj_engine)
    db_cursors, db_types = assert_db_states(proj_engine, 13, 3)
    
    spel_cursors = {'A': None, 'B': None}
    for db_c in db_cursors:
        if db_c.spelling in spel_cursors and db_c.kind.name == 'STRUCT_DECL':
            spel_cursors[db_c.spelling] = db_c

    # verify declaration of the type
    for db_t in db_types:
        if db_t.declaration:
            assert db_t.spelling in spel_cursors
            eq_(spel_cursors[db_t.spelling], db_t.declaration)
    
    # verify the type of the cursor
    for _c in tu.cursor.get_children():
        if _c.location.file: # skip builtin cursors
            assert_cursor_type(_c, proj_engine)


TEST_BUILD_DB_CURSOR_INPUT_2 = '''
class A;
class A;
void func();
'''

@with_param_setup(setup_for_memory_file, TEST_BUILD_DB_CURSOR_INPUT_2)
def test_proj_engine_build_db_cursor_for_def_cursors_1(tu, proj_engine):
    ''' Test the logic that when definition cursor has not been stored
    in the DB, then all declaration cursors will left its 
    definition field None.
    '''

    simple_build_db_cursor(tu.cursor, proj_engine)
    db_cursors, _ = assert_db_states(proj_engine, 3, 2)
    
    # verify that all cursors' definition field is None
    for db_c in db_cursors:
        assert db_c.spelling in ['A', 'func']
        assert db_c.definition is None



def assert_decl_with_def_cursor(tu, proj_engine, cursor_num, type_num):
    simple_build_db_cursor(tu.cursor, proj_engine)
    db_cursors, _ = assert_db_states(proj_engine, cursor_num, type_num)
    db_A_def_cursor = None
    # get the A definition cursor
    for db_c in db_cursors:
        if db_c.spelling == 'A' and db_c.is_definition:
            db_A_def_cursor = db_c
    
    assert db_A_def_cursor
    for db_c in db_cursors:
        if db_c.spelling == 'A':
            if db_c.is_definition:
                assert db_c.definition is None
            else:
                assert db_c.definition
                eq_(db_A_def_cursor, db_c.definition)
        else:
            assert db_c.definition is None # foo


TEST_BUILD_DB_CURSOR_INPUT_3 = '''
class A;
class A;
void func();

class A {};
'''


@with_param_setup(setup_for_memory_file, TEST_BUILD_DB_CURSOR_INPUT_3)
def test_proj_engine_build_db_cursor_for_def_cursors_2(tu, proj_engine):
    ''' Test the logic that when definition cursor has not been stored
    in the DB, then all declaration cursors will left its 
    definition field None. Once the definition cursor is found,
    then all declaration cursors in DB will be updated with its definition
    field.
    '''
    
    assert_decl_with_def_cursor(tu, proj_engine, 4, 2)


TEST_BUILD_DB_CURSOR_INPUT_4 = '''
class A;
class A;
void func();

class A {};
class A;
'''

@with_param_setup(setup_for_memory_file, TEST_BUILD_DB_CURSOR_INPUT_4)
def test_proj_engine_build_db_cursor_for_def_cursors_3(tu, proj_engine):
    ''' Test the logic that after the definition cursor has been stored in DB,
    all declaration cursors will have the definition field pointing to the 
    same definition.
    '''
    
    assert_decl_with_def_cursor(tu, proj_engine, 5, 2)


def assert_ref_cursor(cursor, proj_engine):
    db_cursor = db.Cursor.get_db_cursor(cursor, proj_engine)
    assert db_cursor
    assert is_db_cursor(db_cursor)
    if cursor.referenced:
        if cursor == cursor.referenced:
            assert db_cursor.referenced is None
        else:
            assert db_cursor.referenced
            assert_cursor_equal(cursor.referenced, db_cursor.referenced)
    else:
        assert db_cursor.referenced is None

    for child in cursor.get_children():
        assert_ref_cursor(child, proj_engine)

def assert_db_states_and_ref_cursors(tu, proj_engine, cursor_num, type_num):
    simple_build_db_cursor(tu.cursor, proj_engine)
    assert_db_states(proj_engine, cursor_num, type_num)

    # verify the type of the cursor
    for _c in tu.cursor.get_children():
        if _c.location.file: # skip builtin cursors
            assert_ref_cursor(_c, proj_engine)

TEST_BUILD_DB_CURSOR_INPUT_5 = '''
void foo()
{
    int a = 1;
    int b = a;
}
'''

@with_param_setup(setup_for_memory_file, TEST_BUILD_DB_CURSOR_INPUT_5)
def test_proj_engine_build_db_cursor_for_ref_cursor_1(tu, proj_engine):
    assert_db_states_and_ref_cursors(tu, proj_engine, 9, 2)


TEST_BUILD_DB_CURSOR_INPUT_6 = '''
class A
{
    int m_i;
    void memfun()
    {
        int b = m_i;
    }
};
'''

@with_param_setup(setup_for_memory_file, TEST_BUILD_DB_CURSOR_INPUT_6)
def test_proj_engine_build_db_cursor_for_ref_cursor_2(tu, proj_engine):
    assert_db_states_and_ref_cursors(tu, proj_engine, 8, 3)

@with_param_setup(setup_for_memory_file, TEST_CURSOR_REF_INPUT2)
def test_proj_engine_build_db_cursor_for_ref_cursor_3(tu, proj_engine):
    assert_db_states_and_ref_cursors(tu, proj_engine, 17, 4)

TEST_BUILD_DB_CURSOR_INPUT_7 = '''
template<typename T> T foo(T t) { return t; }
void bar() { foo(1); }
'''

@with_param_setup(setup_for_memory_file, TEST_BUILD_DB_CURSOR_INPUT_7)
def test_proj_engine_build_db_cursor_for_ref_cursor_4(tu, proj_engine):
    assert_db_states_and_ref_cursors(tu, proj_engine, 15, 7)

TEST_BUILD_DB_CURSOR_INPUT_8 = '''
class A;
A* foo(A* a) { return a; }
'''

@with_param_setup(setup_for_memory_file, TEST_BUILD_DB_CURSOR_INPUT_8)
def test_proj_engine_build_db_cursor_for_ref_cursor_5(tu, proj_engine):
    assert_db_states_and_ref_cursors(tu, proj_engine, 9, 3)


def assert_left_right(tu, proj_engine, left = 0):
    
    def impl(cursor, left):
        db_cursor = db.Cursor.get_db_cursor(cursor, proj_engine)
        assert db_cursor
        assert is_db_cursor(db_cursor)
        eq_(left, db_cursor.left)
        
        left += 1
        for child in cursor.get_children():
            left = impl(child, left) + 1
    
        right = left
        eq_(right, db_cursor.right)
        return right
    
    child_left = left
    if isinstance(tu, cindex.TranslationUnit):
        for _c in tu.cursor.get_children():
            if _c.location.file:
                child_left = impl(_c, child_left) + 1
    else:
        child_left = impl(tu, child_left) + 1
    
    return child_left - 1 if child_left != left else left

@with_param_setup(setup_for_memory_file, TEST_BUILD_DB_CURSOR_INPUT_6)
def test_proj_engine_build_db_cursor_for_left_right(tu, proj_engine):
    simple_build_db_cursor(tu.cursor, proj_engine)
    assert_db_states(proj_engine, 8, 3)
    assert_left_right(tu, proj_engine)
    

TEST_BUILD_DB_TREE_1 = '''
int a = 1;
int main()
{
    int b = a;
    return 0;
}
'''

@with_param_setup(setup_for_memory_file, TEST_BUILD_DB_TREE_1)
def test_proj_engine_build_db_tree(tu, proj_engine):
    proj_engine.build_db_tree(tu.cursor)
    
    actual_file_names = set(_file.name for _file in
                            proj_engine.get_session().query(db.File).all())
    set_eq(['t.cpp'], actual_file_names)
    
    assert_db_states(proj_engine, 10, 2)
    assert_left_right(tu, proj_engine)
    for _c in tu.cursor.get_children():
        if _c.location.file:
            assert_cursor_type(_c, proj_engine)
            assert_ref_cursor(_c, proj_engine)


def assert_build_db_cursor(proj_engine, tus, expecteds):
    eq_(len(tus), len(expecteds))
    
    right = 0
    for tu, expected in zip(tus, expecteds):
        pending_files = db.File.get_pending_filenames(tu, proj_engine)
        proj_engine.build_db_tree(tu.cursor)
    
        actual_file_names = set(_file.name for _file in
                                proj_engine.get_session().query(db.File).all())
        set_eq(expected[0], actual_file_names)
        
        assert_db_states(proj_engine, expected[1], expected[2])
        for _c in tu.cursor.get_children():
            _file = _c.location.file
            if (_file or _c.location.line > 0) and _file.name in pending_files:
                right = assert_left_right(_c, proj_engine, right) + 1
                assert_cursor_type(_c, proj_engine)
                assert_ref_cursor(_c, proj_engine)
        
        right += 19

def test_proj_engine_build_db_tree_with_multiple_files():
    SOURCE_1 = '''
char a = 'a';
char foo() { return a; }
'''
    SOURCE_2 = '''
int b = 1;
int bar() { return b; }
'''
    
    proj_engine = db.ProjectEngine('test', is_in_memory = True)
    t1_tu = get_tu_from_text(SOURCE_1, 't1.cpp')
    t2_tu = get_tu_from_text(SOURCE_2, 't2.cpp')
    
    assert_build_db_cursor(proj_engine, [t1_tu, t2_tu],
                           [(['t1.cpp'], 7, 2),
                            (['t1.cpp', 't2.cpp'], 14, 4)])


def test_proj_engine_build_db_tree_with_multiple_files_2():
    PROJ_ENG_TEST_DIR = os.path.join(_TEST_DATA_DIR, 'db', 'proj_engine')
    main1_path = os.path.join(PROJ_ENG_TEST_DIR, 'main1.cpp')
    main2_path = os.path.join(PROJ_ENG_TEST_DIR, 'main2.cpp')
    
    proj_engine = db.ProjectEngine('test', is_in_memory = True)
    main1_tu = get_tu(main1_path)
    main2_tu = get_tu(main2_path)
    
    expecteds = [([os.path.join(PROJ_ENG_TEST_DIR, _f) 
                   for _f in ['A.h', 'B.h', 'main1.cpp']], 
                  43, 15),
                 ([os.path.join(PROJ_ENG_TEST_DIR, _f)
                   for _f in ['A.h', 'B.h', 'main1.cpp', 'main2.cpp']],
                  62, 18)]
    assert_build_db_cursor(proj_engine, [main1_tu, main2_tu], expecteds)
    
