from reshaper.util import get_tu, get_cursors_if
from reshaper.util import walk_ast, get_function_signature
from clang.cindex import CursorKind
import os
from functools import partial
from nose.tools import eq_, with_setup

INPUT_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
tu = None


def setup():
    global tu
    source = os.path.join(INPUT_DIR, 'class.cpp')
    tu = get_tu(source)
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
def test_get_cursors_if():
    cursors = get_cursors_if(tu, lambda c: c.spelling == 'A')
    assert(len(cursors) == 2) # the class itself and the constructor
    for cursor in cursors:
        assert(cursor.spelling == 'A')

    assert([cursor.kind for cursor in cursors] ==
           [CursorKind.CLASS_DECL, CursorKind.CONSTRUCTOR])

    # with other conditions
    cursors = get_cursors_if(tu,
                             lambda c: c.kind == CursorKind.CLASS_DECL)
    assert(len(cursors) == 1) # the class itself
    assert(cursors[0].kind == CursorKind.CLASS_DECL)
    assert(cursors[0].spelling == 'A')

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

    namespace.node_count = 0
    walk_ast(tu, partial(count_level_node, expected_level = 1))
    eq_(6, namespace.node_count)

    namespace.node_count = 0
    walk_ast(tu, partial(count_level_node, expected_level = 2))
    eq_(20, namespace.node_count)
    
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
    
