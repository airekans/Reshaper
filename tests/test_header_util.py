'''
Created on Apr 4, 2013

@author: liangzhao
'''
import unittest
import os
import reshaper.semantic as sem
from clang.cindex import CursorKind
from reshaper.ast import get_tu, save_ast

class Test(unittest.TestCase):
    TEST_HEADER_FILE = os.path.join(os.path.dirname(__file__),
                                     'test_data','test.h')
    
    def setUp(self):
        save_ast(Test.TEST_HEADER_FILE)
        self.__tu_cursor = get_tu(Test.TEST_HEADER_FILE, config_path = None).cursor
        assert(self.__tu_cursor)
    

    def test_get_class_decl_cursor(self):
        cursor = sem.get_class_cursor_in_file(self.__tu_cursor, 'A', \
                                          Test.TEST_HEADER_FILE)
        self.assertEqual('A', cursor.spelling)  
        self.assertEqual(CursorKind.CLASS_DECL, cursor.kind)
        
    def test_get_member_vars(self):
        cursor = sem.get_class_cursor_in_file(self.__tu_cursor, 'A', \
                                          Test.TEST_HEADER_FILE)
        member_vars = sem.get_non_static_var_names(cursor)
        self.assertEqual(['m_i1', 'm_i2', 'm_i3', 'm_i4', 'm_d',\
                          'm_p1', 'm_s1', 'm_p2', 'm_p3', 'm_x'],
                         member_vars)
        
        non_pt_members = sem.get_non_static_nonpt_var_names(cursor)
        self.assertEqual(['m_i1', 'm_i2', 'm_i3', 'm_i4', 'm_d', 'm_s1', 'm_x'],
                         non_pt_members)
        
        pointer_vars = sem.get_non_static_pt_var_names(cursor)
        self.assertEqual(['m_p1', 'm_p2', 'm_p3'], pointer_vars)
        
    def test_get_all_class_decl_cursors(self):
        cursors = sem.get_all_class_cursors(self.__tu_cursor, \
                                           Test.TEST_HEADER_FILE)
        cursor_names = [c.spelling for c in cursors]
        self.assertEqual(['X', 'string', 'A', 'B', 'B1', 'C'], cursor_names)
        
    def test_get_all_class_names(self):
        cursor_names = sem.get_all_class_names(self.__tu_cursor, \
                                           Test.TEST_HEADER_FILE)
        self.assertEqual(['X', 'string', 'A', 'B', 'B1', 'C'], cursor_names)
        
        cursor_names = sem.get_all_class_names(self.__tu_cursor, None)
        self.assertEqual(['X', 'string', 'A', 'B', 'B1', 'C'], cursor_names)
    
if __name__ == "__main__":
    unittest.main()
