from reshaper.ast import    FlyweightBase, \
                            CursorCache, CursorLazyLoad, \
                            LocationCache
from .util import get_tu_from_text
                
from nose.tools import eq_
from clang.cindex import TranslationUnit
import os
from reshaper.util import get_cursor


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
    _a2 =  ClassA('_a2')
    
    eq_(id(FlywightA1(_a1)), id(FlywightA1(_a1)))
    assert(id(FlywightA1(_a1)) != id(FlywightA1(_a2)))
    assert(id(FlywightA1(_a1)) != id(FlywightA2(_a1)))
    
    eq_(FlywightA1(_a1), _a1)
    assert(FlywightA1(_a1) < _a2)
    
    
    class File(object):
        def __init__(self, name):
            self.name = name
            
    class Location(object):
        def __init__(self, _file, line, column):
            self.file = _file
            self.line = line
            self.column = column
    
    file_ = File('test.cpp')
    line = 100
    column = 5
    
    loc1 = Location(file_, line, column)
    loc2 = Location(file_, line, column)
    
    assert(id(loc1) != id(loc2))
        
    eq_( id(LocationCache(loc1)), \
         id(LocationCache(loc2)))       
            
    

INPUT_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
def testCursorCache():
    source = os.path.join(INPUT_DIR, 'class.cpp')
    _tu = TranslationUnit.from_source(source)
    assert(_tu)
    assert(_tu.cursor)
    cursor_cache = CursorCache(_tu.cursor, source) 
    
    cc_func = get_cursor(cursor_cache, 'result_test_fun')
    assert(isinstance(cc_func, CursorCache))
    
    cc_class = cc_func.semantic_parent
    assert(cc_class is None) #can't find cursor not defined in source
    
    cursor_cache.update_ref_cursors() 
    cc_class = cc_func.semantic_parent
    assert(isinstance(cc_class, CursorLazyLoad)) #ref cursor defined in other file
    
    
    