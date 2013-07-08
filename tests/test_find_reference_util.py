'''test_find_reference_util.py -- unittest for
find_reference_util.py
'''

from clang.cindex import CursorKind, TranslationUnit
from nose.tools import eq_
from reshaper.util import get_cursor_with_location
from reshaper.semantic import get_cursors_add_parent
from reshaper.find_reference_util import filter_cursors_by_usr, \
        get_usr_if_caller, ClassInfo, FileClassInfo,\
        CallInfo, walk_ast_add_caller, get_usr_of_declaration_cursor,\
        get_declaration_location_str, compare_file_name
from .util import get_tu_from_text
from functools import partial

filter_usr_test_input = """\
class TestClass
{
public:
    void TargetFunc()
    {
    }
}

namespace TestNS
{
    void TargetFunc()
    {
    }
}

void CallFunc()
{
    TestClass *pTC = new TestClass();
    pTC->TargetFunc();

    TestNS::TargetFunc();
}
"""

class_info_test = """\
class TestClass
{
public:
    TestClass();
    TestClass(int x) : m_x(x) {}
    ~TestClass(){}

    void class_func1();
    bool class_func2() {}

    static void static_func() {}
private:
    int m_x;
    double m_d;
    long* m_pL;
    char* m_ch;
};
"""

class_info_from_file_test = """\
class TestClass1
{
};

class TestClass2 : public TestClass1
{
public:
    TestClass2();
};

struct TestStruct
{
int m_int;
double m_double;
};
"""

walk_ast_add_caller_test_file = """\
void call_func()
{
}

namespace {
    void namespace_func()
    {
    }
}

class TestClass
{
public:
    void class_func()
    {
        call_func();
        m_int = 10;
    }

public:
    double m_public;

private:
    int m_int;
};

void global_func()
{
    ::namespace_func();
    call_func();
    TestClass t;
    t.class_func();
    t.m_public = 0.0;
}
"""

cursor_location_usr_test_file = """\
void call_func();
void test_func()
{
}
"""

def test_get_declaration_location_usr():
    '''test get_declaration_location_str
    '''
    text_tu = get_tu_from_text(cursor_location_usr_test_file)
    cursor1 = get_cursor_with_location(text_tu, "call_func", 1)
    cursor2 = get_cursor_with_location(text_tu, "test_func", 2)
    none_cursor = get_cursor_with_location(text_tu, "TestClass", 4)

    location_cursor1 = get_declaration_location_str(cursor1)
    location_cursor2 = get_declaration_location_str(cursor2)
    location_none = get_declaration_location_str(none_cursor)
    eq_("t.cpp-1-6", location_cursor1)
    eq_("t.cpp-2-6", location_cursor2)
    assert(location_none is None)


def test_caller_callee_str_caller():
    '''test CallInfo caller
    '''
    test_str = CallInfo("")
    caller1 = "testfile-14-10"
    caller2 = "testfile-24-10"

    test_str.add_caller(caller1)
    eq_(caller1, test_str.get_caller())
    test_str.add_caller(caller1)
    eq_(caller1, test_str.get_caller())
    eq_(len(test_str.get_caller_list()), 1)

    test_str.add_caller(caller2)
    expect_caller = "%s,%s" % (caller1, caller2)
    eq_(expect_caller, test_str.get_caller())
    eq_(len(test_str.get_caller_list()), 2)

    expect_str = "caller|%s;callee|" % expect_caller
    eq_(expect_str, test_str.get_callers_callees_str())

    test_str.clear()
    eq_(test_str.get_caller(), "")

def test_caller_callee_str_callee():
    '''test CallInfo callee
    '''
    test_str = CallInfo("")
    callee1 = "testfile-34-10"
    callee2 = "testfile-44-10"

    test_str.add_callee(callee1)
    eq_(callee1, test_str.get_callee())
    test_str.add_callee(callee1)
    eq_(callee1, test_str.get_callee())
    eq_(len(test_str.get_callee_list()), 1)

    test_str.add_callee(callee2)
    expect_callee = "%s,%s" % (callee1, callee2)
    eq_(expect_callee, test_str.get_callee())
    eq_(len(test_str.get_callee_list()), 2)

    expect_str = "caller|;callee|%s" % expect_callee
    eq_(expect_str, test_str.get_callers_callees_str())

    test_str.clear()
    eq_(test_str.get_callee(), "")

def test_classes_info():
    '''test classes info from tu
    '''
    text_tu = get_tu_from_text(class_info_from_file_test)
    classes_info_test = FileClassInfo(filename = None, source_tu = text_tu)
    class_names = classes_info_test.get_class_list()
    eq_(len(class_names), 3)

    TestClass1_info = classes_info_test.get_class_info_with_name("TestClass1")
    TestClass2_info = classes_info_test.get_class_info_with_name("TestClass2")
    TestStruct_info = classes_info_test.get_class_info_with_name("TestStruct")
    assert(isinstance(TestClass1_info, ClassInfo))
    assert(isinstance(TestClass2_info, ClassInfo))
    assert(isinstance(TestStruct_info , ClassInfo))


def test_class_info():
    '''test class ClassInfo
    '''
    text_tu = get_tu_from_text(class_info_test)
    class_cursor = get_cursor_with_location(text_tu, "TestClass", 1)
    eq_(class_cursor.kind, CursorKind.CLASS_DECL)
    testclass_mem_info = ClassInfo(class_cursor)

    mem_list = testclass_mem_info.get_mem_list()
    eq_(len(mem_list), 4)
    assert("int m_x" in str(mem_list))
    assert("double m_d" in str(mem_list))
    assert("long* m_pL" in str(mem_list))
    assert("char* m_ch" in str(mem_list))

    func_list = testclass_mem_info.get_mem_func_list()
    eq_(len(func_list), 6)
    assert("TestClass" in str(func_list))
    assert("~TestClass" in str(func_list))
    assert("class_func1" in str(func_list))
    assert("class_func2" in str(func_list))
    assert("static_func" in str(func_list))
    

def test_filter_cursurs_by_usr():
    '''test function filter_cursors_by_usr
    '''
    _tu = get_tu_from_text(filter_usr_test_input)
    spelling = "TargetFunc"
    target_cursor = get_cursor_with_location(_tu, spelling, 4)
    target_usr = target_cursor.get_usr()

    candidate_curs = get_cursors_add_parent(_tu, spelling)

    eq_(len(candidate_curs), 7)
    final_curs = filter_cursors_by_usr(candidate_curs, target_usr)
    eq_(len(final_curs), 2)
    eq_(final_curs[0].location.line, 4)
    eq_(final_curs[1].location.line, 19)

def test_get_usr_if_caller():
    '''test get_usr_if_caller
    '''
    text_tu = get_tu_from_text(filter_usr_test_input)
    class_decl_cursor = get_cursor_with_location(text_tu, "TestClass", 1)
    class_decl_test = get_usr_if_caller(class_decl_cursor)
    assert(class_decl_test is None)

    cxx_method_cursor = get_cursor_with_location(text_tu, "TargetFunc", 4)
    cxx_method_test = get_usr_if_caller(cxx_method_cursor)
    assert(cxx_method_test is not None)

    func_defin_cursor = get_cursor_with_location(text_tu, "CallFunc", 16)
    func_defin_test = get_usr_if_caller(func_defin_cursor)
    assert(func_defin_test is not None)

    func_ref_cursor = get_cursor_with_location(text_tu, "TargetFunc", 19)
    func_ref_test = get_usr_if_caller(func_ref_cursor)
    assert(func_ref_test is None)

def walk_ast_add_caller_visitor(cursor, caller_usr, location, call_info_dict):
    """used as visitor for walk_ast_add_caller
    """
    if cursor is None or not cursor.kind or caller_usr is None:
        return
    if cursor.kind == CursorKind.CALL_EXPR or \
            cursor.kind == CursorKind.UNEXPOSED_EXPR or \
            cursor.kind == CursorKind.COMPOUND_STMT or \
            cursor.kind == CursorKind.BINARY_OPERATOR:
                return

    decl_usr = get_usr_of_declaration_cursor(cursor)
    if decl_usr is None:
        return

    if decl_usr == caller_usr:
        return

    cursor_location = get_declaration_location_str(cursor)

    cursor_info  = ""
    caller_info = ""
    if cursor_location in call_info_dict.keys():
        cursor_info = call_info_dict[cursor_location]
    if location in call_info_dict.keys():
        caller_info = call_info_dict[location]

    cursor_info_obj = CallInfo(cursor_info)
    caller_info_obj = CallInfo(caller_info)

    cursor_info_obj.add_caller(caller_usr)
    caller_info_obj.add_callee(decl_usr)

    call_info_dict[cursor_location] = cursor_info_obj.get_callers_callees_str()
    call_info_dict[location] = caller_info_obj.get_callers_callees_str()


def test_walk_ast_add_caller():
    """
    test walk_ast_add_caller:

    cursors with information should be
     call_func, namespace_func, TestClass
     , class_func, m_public, m_int, global_func
     and t defined in global_func (total are 8)

     only global_func and class_func have callee;
     1) global_func has callee : namespace_func, TestClass, 
         t, class_func, m_public, call_func
     2) class_func has callee : call_func, m_int
     3) only class_func has both caller and callee
    """
    call_info_dict = {}
    text_tu = get_tu_from_text(walk_ast_add_caller_test_file)
    walk_ast_add_caller(text_tu, \
            partial(walk_ast_add_caller_visitor, call_info_dict = call_info_dict))

    eq_(8, len(call_info_dict))
    with_callee_num = 0
    with_caller_num = 0
    with_callee_and_caller_num = 0
    for key in call_info_dict.keys():
        call_infor = CallInfo(call_info_dict[key])
        caller_str = call_infor.get_caller()
        callee_str = call_infor.get_callee()
        if not caller_str == "":
            with_caller_num += 1
        if not callee_str == "":
            with_callee_num += 1
        if not caller_str == "" and not callee_str == "":
            with_callee_and_caller_num += 1
    eq_(2, with_callee_num)
    eq_(7, with_caller_num)
    eq_(1, with_callee_and_caller_num)

def test_compare_file_name():
    """test compare_file_name
    """
    base_filename = "base.cpp"
    cursor = None
    assert(compare_file_name(cursor, 0, base_filename))

    text_tu = get_tu_from_text(filter_usr_test_input)
    class_decl_cursor = get_cursor_with_location(text_tu, "TestClass", 1)
    assert(not compare_file_name(class_decl_cursor, 0, base_filename))

    cxx_method_cursor = get_cursor_with_location(text_tu, "TargetFunc", 4)
    cxx_method_cursor.location.file.name = "base.h"
    assert(compare_file_name(cxx_method_cursor, 0, base_filename))

