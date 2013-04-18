'''test_find_reference.py -- unittest for semantic.py
'''

from clang.cindex import TranslationUnit
from clang.cindex import Cursor
from clang.cindex import CursorKind
from nose.tools import eq_
import reshaper.semantic as semantic_util
from reshaper.util import get_cursor_with_location
from reshaper.semantic import get_full_qualified_name 

parent_calling_func_test_input = """\
void TargetFunc()
{
}
int testVariable = 0;
void CallMe()
{
    TargetFunc();
}
void Call_CallMe()
{
    int j = 0;
    int u = (1 == true ?testVariable : (testVariable+1));
    CallMe();
    TargetFunc();
}
"""

declaration_test_input = """\
class TestClass
{
public:
    void classFunc()
    {
    }
};

namespace TestName
{
    void nameFunc()
    {
    }
}

namespace
{
    void annoyNameFunc()
    {
    }
}

void GlobalFunc()
{
}

void CallFunc()
{
   TestClass tc;
   tc.classFunc();
   TestName::nameFunc();
   ::annoyNameFunc();
   GlobalFunc();
}
"""

def get_tu_from_text(source):
    '''copy it from util.py, just for test
    '''
    name = 't.cpp'
    args = []
    args.append('-std=c++11')

    return TranslationUnit.from_source(name, args, unsaved_files=[(name,
                                       source)])

def has_child(cursor, is_translation_unit):
    '''called by test_get_cursors_add_parent to 
    test if having got the corrent parent
    '''
    assert(isinstance(cursor, Cursor))

    _has_child = False

    if is_translation_unit:
        assert(not cursor.parent)
    else:
        assert(isinstance(cursor.parent, Cursor))
        for child in cursor.parent.get_children():
            if child == cursor:
                _has_child = True
        assert(_has_child)



def test_get_cursors_add_parent():
    '''test get_cursors_add_parent
    '''
    _tu = get_tu_from_text(parent_calling_func_test_input)
    assert(isinstance(_tu, TranslationUnit))
    spelling = "TargetFunc"
    cursors = semantic_util.get_cursors_add_parent(_tu, spelling)
    for cursor in cursors:
        assert(isinstance(cursor, Cursor))
        has_child(cursor, cursor.location.line == 1)

def test_get_cursor_with_location():
    '''test get_cursor_with_location in reshaper.util
    '''
    _tu = get_tu_from_text(parent_calling_func_test_input)
    assert(isinstance(_tu, TranslationUnit))
    spelling = "testVariable"
    cursor1 = get_cursor_with_location(_tu, spelling, 1, None)
    assert(not cursor1)
    cursor2 = get_cursor_with_location(_tu, spelling, 4, 10)
    assert(not cursor2)
    cursor3 = get_cursor_with_location(_tu, spelling, 12, None)
    assert(isinstance(cursor3, Cursor))
    assert(spelling in cursor3.displayname)
    eq_(cursor3.location.line, 12)
    eq_(cursor3.location.column, 25)
    cursor4 = get_cursor_with_location(_tu, spelling, 12, 41)
    assert(isinstance(cursor4, Cursor))
    assert(spelling in cursor4.displayname)
    eq_(cursor4.location.line, 12)
    eq_(cursor4.location.column, 41)

def test_get_calling_function():
    '''test get_calling_function
    Attention: should make sure cursors have parent attr 
    '''
    _tu = get_tu_from_text(parent_calling_func_test_input)
    assert(isinstance(_tu, TranslationUnit))
    spelling = "TargetFunc"
    cursors = semantic_util.get_cursors_add_parent(_tu, spelling)
    for cur in cursors:
        assert(isinstance(cur, Cursor))
        parent = semantic_util.get_calling_function(cur)
        if cur.location.line == 1:
            assert(not parent)
        elif cur.location.line == 7:
            assert(isinstance(parent, Cursor))
            assert(str("CallMe") in parent.displayname)
        elif cur.location.line == 14:
            assert(isinstance(parent, Cursor))
            assert(str("Call_CallMe") in parent.displayname)

def get_decla_tu():
    '''get _tu for declaration tests
    '''
    _tu = get_tu_from_text(declaration_test_input)
    assert(isinstance(_tu, TranslationUnit))
    return _tu

def test_get_declaration_cursor_class():
    '''use to test get_declaration_cursor and 
    get_semantic_parent_of_decla_cursor of class member function
    '''

    _tu = get_decla_tu()
    spelling = "classFunc"
    curClass = get_cursor_with_location(_tu, spelling, 30, None)
    assert(isinstance(curClass, Cursor))
    decla_cursor = semantic_util.get_declaration_cursor(curClass)
    eq_(decla_cursor.location.line, 4)
    eq_(decla_cursor.kind, CursorKind.CXX_METHOD)
    seman_parent = semantic_util.get_semantic_parent_of_decla_cursor(curClass)
    eq_(seman_parent, decla_cursor.semantic_parent)
    eq_(seman_parent.kind, CursorKind.CLASS_DECL)

def test_get_declaration_cursor_namespace():
    '''use to test get_declaration_cursor and 
    get_semantic_parent_of_decla_cursor of namespace function
    '''
    _tu = get_decla_tu()
    spelling = "nameFunc"
    cur = get_cursor_with_location(_tu, spelling, 31, None)
    assert(isinstance(cur, Cursor))
    decla_cursor = semantic_util.get_declaration_cursor(cur)
    eq_(decla_cursor.location.line, 11)
    eq_(decla_cursor.kind, CursorKind.FUNCTION_DECL)
    seman_parent = semantic_util.get_semantic_parent_of_decla_cursor(cur)
    eq_(seman_parent, decla_cursor.semantic_parent)
    eq_(seman_parent.kind, CursorKind.NAMESPACE)

def test_get_declaration_cursor_annoy_namespace():
    '''use to test get_declaration_cursor and 
    get_semantic_parent_of_decla_cursor of annoymouse namespace function
    '''
    _tu = get_decla_tu()
    spelling = "annoyNameFunc"
    cur = get_cursor_with_location(_tu, spelling, 32, None)
    assert(isinstance(cur, Cursor))
    decla_cursor = semantic_util.get_declaration_cursor(cur)
    eq_(decla_cursor.location.line, 18)
    eq_(decla_cursor.kind, CursorKind.FUNCTION_DECL)
    seman_parent = semantic_util.get_semantic_parent_of_decla_cursor(cur)
    eq_(seman_parent, decla_cursor.semantic_parent)
    eq_(seman_parent.kind, CursorKind.NAMESPACE)

def test_get_declaration_cursor_global_func():
    '''use to test get_declaration_cursor and 
    get_semantic_parent_of_decla_cursor of global function
    '''
    _tu = get_decla_tu()
    spelling = "GlobalFunc"
    cur = get_cursor_with_location(_tu, spelling, 33, None)
    assert(isinstance(cur, Cursor))
    decla_cursor = semantic_util.get_declaration_cursor(cur)
    eq_(decla_cursor.location.line, 23)
    eq_(decla_cursor.kind, CursorKind.FUNCTION_DECL)
    seman_parent = semantic_util.get_semantic_parent_of_decla_cursor(cur)
    eq_(seman_parent, decla_cursor.semantic_parent)
    eq_(seman_parent.kind, CursorKind.TRANSLATION_UNIT)



get_info_test_input = """\
class TestClass
{
public:
    void memFunc(int)
    {
    }
};
namespace TestNamespace
{
    void namespaceFunc(TestClass&)
    {
    }
}
void globalFunc()
{
}
"""

def test_get_full_qualified_name():
    '''test get_full_qualified_name
    '''
    tu_source = get_tu_from_text(get_info_test_input)
    mem_cursor = get_cursor_with_location(tu_source, "memFunc", 4, None)
    assert(isinstance(mem_cursor, Cursor))
    mem_info = get_full_qualified_name(mem_cursor)
    eq_(mem_info, "TestClass::memFunc(int)")

    namespace_cursor = get_cursor_with_location(tu_source, "namespaceFunc", 10, None)
    assert(isinstance(namespace_cursor, Cursor))
    name_info = get_full_qualified_name(namespace_cursor)
    eq_(name_info, "TestNamespace::namespaceFunc(TestClass &)")

    global_cursor = get_cursor_with_location(tu_source, "globalFunc", 14, None)
    assert(isinstance(global_cursor, Cursor))
    global_info = get_full_qualified_name(global_cursor)
    eq_(global_info, "globalFunc()")
    
