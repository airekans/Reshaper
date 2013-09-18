'''
Created on Sep 11, 2013

@author: Jingchuan Chen
'''

import encapsulate_fields
import os
from tests.util import assert_file_equal

def test_encapsulate_fields_wo_field_arg():
    '''test transform_public_fields.py without field argument
    '''
    input_path = os.path.join(os.path.dirname(__file__), 'test_data', 'encapsulate')
    input_file = os.path.join(input_path, 'test_encap.cpp')
    args = [input_file, '-d', input_path, 'A', 'B']
    encapsulate_fields.main(args)
    
    assert_file_equal(os.path.join(input_path, 'test_encap.cpp.ref'),
                      os.path.join(input_path, 'test_encap.cpp.bak'))
    assert_file_equal(os.path.join(input_path, 'test_encap.h.ref'),
                      os.path.join(input_path, 'test_encap.h.bak'))
    
def test_encapsulate_fields_with_field_arg():
    '''test transform_public_fields.py with field argument
    '''
    input_path = os.path.join(os.path.dirname(__file__), 'test_data', 'encapsulate')
    input_file = os.path.join(input_path, 'test_encap.cpp')
    args = [input_file, '-f', 'm_i, m_c', 'A', 'B']
    encapsulate_fields.main(args)
    
    assert_file_equal(os.path.join(input_path, 'test_encap.cpp.ref2'),
                      os.path.join(input_path, 'test_encap.cpp.bak'))
    assert_file_equal(os.path.join(input_path, 'test_encap.h.ref2'),
                      os.path.join(input_path, 'test_encap.h.bak'))