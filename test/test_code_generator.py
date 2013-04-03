'''
Created on 2013-3-5

@author: liangzhao
'''
import code_generator as cg 
import os
from pprint import pprint

TEST_HEADER_FILE = os.path.join(os.path.dirname(__file__), './test_data/test.h')


import unittest
class Test(unittest.TestCase):
    def test_get_member_variables(self):
        member_var_non_pt_expected = ['m_d', 'm_i1', 'm_i2', 'm_i3', 'm_i4', 'm_i5', 'm_i6', 'm_s1', 'm_x']
        member_var_pt_expected = ['m_p1','m_p2','m_p3']
        (member_var_non_pt,member_var_pt) = cg.get_member_variables(TEST_HEADER_FILE, 'A')
        self.assertEqual(member_var_non_pt_expected, member_var_non_pt)
        self.assertEqual(member_var_pt_expected, member_var_pt)
        
    
    def test_generate_code(self):
        cg.generate_code(TEST_HEADER_FILE, 'A')
        
        
import unittest
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
