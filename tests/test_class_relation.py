'''
Created on May 19, 2013

@author: liangzhao
'''
import os, unittest
from reshaper.ast import get_tu, save_ast
from reshaper.util import get_cursor
import reshaper.semantic as sem
import reshaper.header_util as hu

CLASS_RELATION_INPUT_HEADER_FILE = os.path.join(os.path.dirname(__file__),
                                     'test_data','class_relation.h')    
CLASS_RELATION_INPUT_SRC_FILE = os.path.join(os.path.dirname(__file__),
                                     'test_data','class_relation.cpp') 

class TestClassRelation(unittest.TestCase):  
    def setUp(self):
        _tu = get_tu(CLASS_RELATION_INPUT_HEADER_FILE)
        self._cls_cursor = get_cursor(_tu, 'A')
        assert(self._cls_cursor)
        
        self._member2class_results = \
                            [ ['m_x', 'X'],
                              ['m_x1', 'X'],
                              ['m_x2', 'X'],
                              ['m_y1', 'Y'],
                              ['m_y2', 'Y'],
                              ['m_other', 'Other']
                             ]

    
    def _check_member_definition(self, member_name, member_class_name):
        member_type_cursor = get_cursor(self._cls_cursor, 
                                        member_name)
        assert(member_type_cursor)
        def_cursor = sem.get_class_definition(member_type_cursor)
        assert(def_cursor)
        assert(sem.is_class_definition(def_cursor))
        self.assertEqual(member_class_name, def_cursor.spelling)
    
    def _check_non_class_member(self, member_name):
        member_type_cursor = get_cursor(self._cls_cursor, 
                                        member_name)
        assert(member_type_cursor)
        def_cursor = sem.get_class_definition(member_type_cursor)
        assert(not def_cursor)
    
    def test_get_class_definition(self):
        for member_name, cls_name in self._member2class_results:
            self._check_member_definition( member_name, cls_name)
        
        
        self._check_non_class_member('m_i')
        self._check_non_class_member('m_pi')
        self._check_non_class_member('m_pc')
              
    def test_get_member_var_classes(self):
        member_with_definitions = hu.get_member_var_classes(\
                                        self._cls_cursor)
        self.assertEqual(len(self._member2class_results), \
                         len(member_with_definitions))
        
        for (member_name, cls_name), (member_cursor, cls_def_cursor) \
            in zip(self._member2class_results, member_with_definitions):
            self.assertEqual(member_name, member_cursor.spelling)
            self.assertEqual(cls_name, cls_def_cursor.spelling)
            
    
    def test_get_class_callee_class_names(self):
        save_ast(CLASS_RELATION_INPUT_SRC_FILE)
        _tu = get_tu(CLASS_RELATION_INPUT_SRC_FILE)
        cls_cursor = get_cursor(_tu, 'A')
        names = sem.get_used_cls_names(cls_cursor)
        
        expected_names = ['X', 'Z', 'Other']
        self.assertEqual(len(expected_names), len(names))
        self.assertEqual(set(expected_names), set(names)) 
        

if __name__ == '__main__':
    unittest.main()