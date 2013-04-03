'test_find_call_chain.py -- unittest for find'

from clang.cindex import Cursor
from clang.cindex import TranslationUnit
from find_call_chain import get_cursor_info
from reshaper.util import get_cursor_with_location
from reshaper.semantic import get_cursors_add_parent
from reshaper.find_reference_util import get_usr_of_declaration_cursor
from reshaper.find_reference_util import filter_cursors_by_usr
from nose.tools import eq_

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

reference_test_input = """\
class TestClass
{
public:
    void test_func(int)
    {
    }
    void test_func(double)
    {
    }
};
void Call_Func()
{
    TestClass tc;
    tc.test_func(0.0);
}
int main()
{
    TestClass *pTC = new TestClass();
    pTC->test_func(10);
    pTC->test_func(0.0);
    return 0;
}
"""

def get_tu_from_text(source):
    '''copy it from util.py, 
    just for test
    '''
    name = 't.cpp'
    args = []
    args.append('-std=c++11')

    return TranslationUnit.from_source(name, args, unsaved_files=[(name,
                                       source)])

def test_get_cursor_info():
    '''test get_cursor_info
    '''
    tu_source = get_tu_from_text(get_info_test_input)
    mem_cursor = get_cursor_with_location(tu_source, "memFunc", 4, None)
    assert(isinstance(mem_cursor, Cursor))
    mem_info = get_cursor_info(mem_cursor)
    eq_(mem_info, "TestClass::memFunc(int)")

    namespace_cursor = get_cursor_with_location(tu_source, "namespaceFunc", 10, None)
    assert(isinstance(namespace_cursor, Cursor))
    name_info = get_cursor_info(namespace_cursor)
    eq_(name_info, "TestNamespace::namespaceFunc(TestClass &)")

    global_cursor = get_cursor_with_location(tu_source, "globalFunc", 14, None)
    assert(isinstance(global_cursor, Cursor))
    global_info = get_cursor_info(global_cursor)
    eq_(global_info, "globalFunc()")

def fake_find_reference_update_output_contents(tu_source, target_cursor):
    '''as update_output_contents only changes var
    defined in find_call_chain.py, it's hard to test
    , we just verify finding reference here.
    '''
    reference_usr = get_usr_of_declaration_cursor(target_cursor)
    spelling_value = ""
    if target_cursor.is_definition():
        spelling_value = (target_cursor.spelling.split('('))[0]
    else:
        spelling_value = (target_cursor.displayname.split('('))[0]

    refer_curs = get_cursors_add_parent(tu_source, spelling_value)
    final_output = filter_cursors_by_usr(refer_curs, reference_usr)
    return final_output


def test_find_reference_update_output_contents():
    tu_source = get_tu_from_text(reference_test_input)
    spelling = "test_func"
    target_cursor = get_cursor_with_location(tu_source, spelling, 20, None)
    output_curs = fake_find_reference_update_output_contents(tu_source, target_cursor)
    eq_(len(output_curs), 3)

    has_definition_cursor = False
    has_in_call_func_cursor = False
    has_in_main_cursor = False
    for cursor in output_curs:
        if (cursor.spelling is not None and spelling in cursor.spelling) or \
                spelling in cursor.displayname:
            if cursor.location.line == 7:
                has_definition_cursor = True
            elif cursor.location.line == 14:
                has_in_call_func_cursor = True
            elif cursor.location.line == 20:
                has_in_main_cursor = True


    assert(has_definition_cursor)
    assert(has_in_call_func_cursor)
    assert(has_in_main_cursor)

