from reshaper.util import get_tu_from_text
from nose.tools import eq_

def test_get_parent():
    TEST_INPUT = '''\
struct A {
    int a;
    double d;
};

A var_a;
'''

    tu = get_tu_from_text(TEST_INPUT)
    assert(tu)

        
    def check_ast(cursor, parent):
        if cursor.get_parent() is None:
            assert(parent is None)
        else:
            eq_(cursor.get_parent().displayname, parent.displayname)
        
        children_count = 0
        for child in cursor.get_children():
            check_ast(child , cursor)
            children_count += 1

        eq_(children_count, len(cursor.get_children()))

    check_ast(tu.cursor, None)

    
    