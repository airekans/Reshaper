from reshaper.ast import get_static_ast
from .util import get_tu_from_text
from nose.tools import eq_

def test_get_static_ast():
    TEST_INPUT = '''\
struct A {
    int a;
    double d;
};
'''

    tu = get_tu_from_text(TEST_INPUT)
    assert(tu)

    static_ast = get_static_ast(tu)
    assert(static_ast)
    
    def check_ast(ast, cursor, parent):
        if ast.ast_parent is None:
            assert(parent is None)
        else:
            eq_(ast.ast_parent.displayname, parent.displayname)
        eq_(ast.displayname, cursor.displayname)

        for child1, child2 in zip(ast.ast_children, cursor.get_children()):
            check_ast(child1, child2, cursor)

    check_ast(static_ast, tu.cursor, None)
    
