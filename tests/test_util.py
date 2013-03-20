from reshaper.util import get_cursors_if, walk_ast, get_function_signature
from clang.cindex import TranslationUnit
from clang.cindex import CursorKind
import os
from functools import partial
from nose.tools import eq_, with_setup

INPUT_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
tu = None


def setup():
    global tu
    source = os.path.join(INPUT_DIR, 'class.cpp')
    tu = TranslationUnit.from_source(source, ['-std=c++11'])
    assert(tu is not None)

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
    def ns(): pass
    ns.node_count = 0
    def count_level_node(_, level, expected_level = 0):
        if level == expected_level:
            ns.node_count += 1

    walk_ast(tu, count_level_node)
    assert(ns.node_count == 1)

    ns.node_count = 0
    walk_ast(tu, partial(count_level_node, expected_level = 1))
    assert(ns.node_count == 5)

    ns.node_count = 0
    walk_ast(tu, partial(count_level_node, expected_level = 2))
    assert(ns.node_count == 15)
    
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
    eq_(1, len(methods))
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
    
    