from reshaper.ast import get_static_ast
from reshaper.util import get_cursor
from .util import get_tu_from_text
from nose.tools import eq_
from clang.cindex import TypeKind, Cursor

def test_get_static_ast():
    TEST_INPUT = '''\
struct A {
    int a;
    double d;
};

A var_a;
'''

    tu = get_tu_from_text(TEST_INPUT)
    assert(tu)

    static_ast = get_static_ast(tu)
    assert(static_ast)
    
    def check_ast(ast, cursor, parent):
        if ast.get_parent() is None:
            assert(parent is None)
        else:
            eq_(ast.get_parent().displayname, parent.displayname)
        eq_(ast.displayname, cursor.displayname)

        children_count = 0
        for child1, child2 in zip(ast.get_children(), cursor.get_children()):
            check_ast(child1, child2, cursor)
            children_count += 1

        eq_(children_count, len(ast.get_children()))

    check_ast(static_ast, tu.cursor, None)

    # test invalidate the static AST
    cursor_var_a = get_cursor(static_ast, "var_a")
    static_cursor_A = get_cursor(static_ast, "A")
    assert(static_cursor_A.is_definition())
    
    var_a_type = cursor_var_a.type
    eq_(TypeKind.RECORD, var_a_type.kind)

    cursor_A = var_a_type.get_declaration()
    assert(isinstance(cursor_A, Cursor))
    assert(not hasattr(cursor_A, "get_parent"))