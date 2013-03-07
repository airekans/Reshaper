'''
Created on 2013-3-5

@author: liangzhao
'''
import code_generator as cg 
import os
from pprint import pprint

TEST_HEADER_FILE = os.path.join(os.path.dirname(__file__), './test_data/test.h')

def test_get_member_variables():
    member_var = cg.get_member_variables(TEST_HEADER_FILE, 'A')
    pprint(member_var)
    pass

def test_generate_code():
    cg.generate_code(TEST_HEADER_FILE, 'A')
