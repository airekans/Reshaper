'''
Created on Sep 11, 2013

@author: jcchentmp
'''

import transform_public_fields
import os
from tests.util import assert_file_content

def test_transform_public_fields():
    '''test transform_public_fields.py
    '''
    input_path = os.path.join(os.path.dirname(__file__), 'test_data', 'transform')
    input_file = os.path.join(input_path, 'test_trs.cpp')
    args = [input_file, 'A', 'B']
    transform_public_fields.main(args)
    
    with open(os.path.join(input_path, 'test_trs.cpp.ref'), 'r') as fp:
        expected = fp.read()
    assert_file_content(expected, os.path.join(input_path, 'test_trs.cpp.bak'))
    
    with open(os.path.join(input_path, 'test_trs.h.ref'), 'r') as fp:
        expected = fp.read()    
    assert_file_content(expected, os.path.join(input_path, 'test_trs.h.bak'))