from reshaper.util import get_tu, get_cursors_if
from reshaper.util import get_cursor, get_cursor_if, get_cursors
from reshaper.util import walk_ast, get_function_signature
from reshaper.util import get_cursor_with_location
from reshaper.util import get_full_qualified_name 
from clang.cindex import Cursor
from clang.cindex import CursorKind
from clang.cindex import TranslationUnit
import os
from functools import partial
from nose.tools import eq_, with_setup
from .util import get_tu_from_text


INPUT_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
tu = None


def setup():
    global tu
    source = os.path.join(INPUT_DIR, 'class.cpp')
    tu = get_tu(source, config_path = None)
    assert(tu is not None)


def test_get_tu():
    # check whether it can handle header file
    source = os.path.join(INPUT_DIR, 'header.h')
    tu = get_tu(source)
    eq_(0, len(tu.diagnostics))
    
    source = os.path.join(INPUT_DIR, 'class.cpp')
    tu = get_tu(source)
    eq_(0, len(tu.diagnostics))

    source = os.path.join(INPUT_DIR, 'B.cpp')
    tu = get_tu(source)
    eq_(0, len(tu.diagnostics))
    
    # To pass the following test, you should write a ".reshaper.cfg" file
    # under current directory or home directory with the following section
    # [Clang Options]
    # include_paths=/path/to/c++/std,/other/default/include/path

    # source = os.path.join(INPUT_DIR, 'include_sys_header.h')
    # tu = get_tu(source)
    # eq_(0, len(tu.diagnostics))


@with_setup(setup)
def test_get_cursor():
    # test get existing cursor
    cursor = get_cursor(tu, 'A')
    assert(cursor is not None)
    eq_(cursor.spelling, 'A')

    cursor = get_cursor(tu, 'bar')
    assert(cursor is not None)
    eq_(cursor.spelling, 'bar')
    
    # test get non-existing cursor
    assert(get_cursor(tu, 'non_exist_node') is None)

@with_setup(setup)
def test_get_cursor_if():
    # test get existing cursor
    cursor = get_cursor_if(tu, lambda c: c.spelling == 'A')
    assert(cursor is not None)
    eq_(cursor.spelling, 'A')

    cursor = get_cursor_if(tu, lambda c: c.kind == CursorKind.CXX_METHOD)
    assert(cursor is not None)
    eq_(cursor.spelling, 'foo')
    
    # test get non-existing cursor
    assert(get_cursor_if(tu, lambda c: c.spelling == 'non_exist') is None)
    
@with_setup(setup)
def test_get_cursors():
    # test get existing cursor
    cursors = get_cursors(tu, 'result_test_fun')
    eq_(2, len(cursors))
    for cursor in cursors:
        eq_('result_test_fun', cursor.spelling)

    # test get non-existing cursor
    eq_(0, len(get_cursors(tu, 'non_exist')))

@with_setup(setup)
def test_get_cursors_if():
    cursors = get_cursors_if(tu, lambda c: c.spelling == 'A')
    eq_(len(cursors), 2) # the class itself and the constructor
    for cursor in cursors:
        eq_(cursor.spelling, 'A')

    eq_([cursor.kind for cursor in cursors],
        [CursorKind.CLASS_DECL, CursorKind.CONSTRUCTOR])

    # with other conditions
    cursors = get_cursors_if(tu,
                             lambda c: c.kind == CursorKind.CLASS_DECL)
    eq_(len(cursors), 1) # the class itself
    eq_(cursors[0].kind, CursorKind.CLASS_DECL)
    eq_(cursors[0].spelling, 'A')

    # test with transform_fun
    cursors = get_cursors_if(tu,
                             lambda c: c.kind == CursorKind.CXX_METHOD and
                                       c.spelling == 'result_test_fun',
                             transform_fun = lambda c: c.spelling)

    eq_(['result_test_fun', 'result_test_fun'], cursors)
    

@with_setup(setup)
def test_walk_ast():
    def namespace():
        pass
    namespace.node_count = 0

    def count_level_node(_, level, expected_level = 0):
        if level == expected_level:
            namespace.node_count += 1

    walk_ast(tu, count_level_node)
    eq_(1, namespace.node_count)

    cursor_A = get_cursor(tu, 'A')
    namespace.node_count = 0
    walk_ast(cursor_A, partial(count_level_node, expected_level = 1))
    eq_(14, namespace.node_count)

    namespace.node_count = 0
    walk_ast(cursor_A, partial(count_level_node, expected_level = 2))
    eq_(19, namespace.node_count)

    # test with is_visit_subtree_fun
    namespace.node_count = 0
    walk_ast(cursor_A, partial(count_level_node, expected_level = 2),
             lambda _, level: level <= 2)
    eq_(19, namespace.node_count)
    
    namespace.node_count = 0
    walk_ast(cursor_A, partial(count_level_node, expected_level = 2),
             lambda _, level: level < 2)
    eq_(0, namespace.node_count)
    
@with_setup(setup)
def test_get_function_signature_with_fun_no_params():
    # function with no parameters
    expected_fun_sig = "void foo()"
    
    methods = get_cursors_if(tu,
                             (lambda c: c.kind == CursorKind.CXX_METHOD and
                              c.spelling == 'foo'))
    eq_(1, len(methods))
    eq_(expected_fun_sig, get_function_signature(methods[0]))

@with_setup(setup)
def test_get_function_signature_with_fun_params():
    # function with parameters
    expected_fun_sig = "int bar(double d)"
    
    methods = get_cursors_if(tu,
                             (lambda c: c.kind == CursorKind.CXX_METHOD and
                              c.spelling == 'bar'))
    eq_(1, len(methods))
    eq_(expected_fun_sig, get_function_signature(methods[0]))

    # parameter of User defined type
    expected_fun_sig = "TestStruct result_test_fun(TestStruct*)"
    
    methods = get_cursors_if(tu,
                             (lambda c: c.kind == CursorKind.CXX_METHOD and
                              c.spelling == 'result_test_fun'))
    eq_(2, len(methods))
    eq_(expected_fun_sig, get_function_signature(methods[0]))

@with_setup(setup)
def test_get_function_signature_with_complex_return_type_fun():
    # function with parameters
    expected_fun_sig = "double (*return_fun_fun(int, double))(int, double)"
    
    methods = get_cursors_if(tu,
                             (lambda c: c.kind == CursorKind.CXX_METHOD and
                              c.spelling == 'return_fun_fun'))
    eq_(1, len(methods))
    eq_(expected_fun_sig, get_function_signature(methods[0]))

@with_setup(setup)
def test_get_function_signature_with_multiline_function():
    expected_fun_sig = \
"""static bool static_multiline_fun(
     const int i,
     const double d)"""
    
    methods = get_cursors_if(tu,
                             (lambda c: c.kind == CursorKind.CXX_METHOD and
                              c.spelling == 'static_multiline_fun'))
    eq_(1, len(methods))
    eq_(expected_fun_sig, get_function_signature(methods[0]))


@with_setup(setup)
def test_get_function_signature_with_error_cursor():
    # create a cursor return 0 token
    methods = get_cursors_if(tu,
                             (lambda c: c.kind == CursorKind.CXX_METHOD and
                              c.spelling == 'foo'))
    eq_(1, len(methods))
    
    method_cursor = methods[0]
    method_cursor.get_tokens = lambda : []
    eq_("", get_function_signature(method_cursor))
    

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


