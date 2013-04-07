'm_p2''''
Created on Apr 4, 2013

@author: liangzhao
'''
import unittest
import os
import header_util as hu
from clang.cindex import CursorKind

class Test(unittest.TestCase):
    TEST_HEADER_FILE = os.path.join(os.path.dirname(__file__), \
                                     './test_data/test.h')
    
    def setUp(self):
        self.__tu_cursor = hu.parse(Test.TEST_HEADER_FILE).cursor
        assert(self.__tu_cursor)

    def test_get_class_decl_cursor(self):
        cursor = hu.get_class_decl_cursor(self.__tu_cursor, 'A')
        self.assertEqual('A', cursor.spelling)  
        self.assertEqual(CursorKind.CLASS_DECL, cursor.kind)
    def test_get_member_vars(self):
        cursor = hu.get_class_decl_cursor(self.__tu_cursor, 'A')
        member_vars = hu.non_static_var_names(cursor)
        self.assertEqual([ 'm_d', 'm_i1', 'm_i2', 'm_i3', 'm_i4', \
                           'm_p1', 'm_p2', 'm_p3', 'm_s1', 'm_x'],
                         member_vars)
        non_pt_members = hu.non_static_nonpt_var_names(cursor)
        self.assertEqual(['m_d', 'm_i1', 'm_i2', 'm_i3', 'm_i4', 'm_s1', 'm_x'],
                         non_pt_members)
        pointer_vars = hu.non_static_pt_var_names(cursor)
        self.assertEqual(['m_p1','m_p2','m_p3'], pointer_vars)

if __name__ == "__main__":
    unittest.main()
