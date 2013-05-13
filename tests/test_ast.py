from reshaper.ast import get_tu_from_text, FlyweightBase
from nose.tools import eq_

def test_get_parent():
    TEST_INPUT = '''\
struct ClassA {
    int a;
    double d;
};

ClassA var_a;
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
    
    
def test_flyweightbase():
    ''' test for FlyweightBase'''
    class ClassA(object):
        ''' test class as input for FlyWeight'''
        def __init__(self, name):
            self.name = name
                
    class FlywightA1(FlyweightBase):
        '''FlywightA1 '''
        def __init__(self, obj_a):
            FlyweightBase.__init__(self, obj_a)
            
    class FlywightA2(FlyweightBase):
        ''' FlywightA2 '''
        def __init__(self, obj_a):
            FlyweightBase.__init__(self, obj_a)
            
    _a1 = ClassA('_a1')
    a11 = ClassA('_a1')
    a2 =  ClassA('a2')
    
    eq_(id(FlywightA1(_a1)), id(FlywightA1(a11)))
    assert(id(FlywightA1(_a1)) != id(FlywightA1(a2)))
    
    assert(id(FlywightA1(_a1)) != id(FlywightA2(_a1)))
    
    