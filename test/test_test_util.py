'''
Created on 2013-3-5

@author: liangzhao
'''

import test_util as tu
import os

DATA_PATH = TEST_HEADER_FILE = os.path.join(os.path.dirname(__file__), 'test_data')

import unittest
class Test(unittest.TestCase):
    def test_compare_generate_golden_file(self):
        golden_file_path = os.path.join(DATA_PATH,'golden1.txt')
        if os.path.isfile(golden_file_path):
            os.remove(golden_file_path)
            assert(not os.path.isfile(golden_file_path))
            
        obj = [1,2,3]
        
        is_equal, msg = tu.compare(obj, golden_file_path)
        assert(is_equal)
        assert(msg == '')
        
    def test_compare_with_golden(self):
        golden_file_path = os.path.join(DATA_PATH,'golden2.txt')
        obj = [1,2,3]
        obj1 = [1,2]
        golden_file = open(golden_file_path,'w')
        import pickle
        pickle.dump(obj,golden_file)
        golden_file.close()
        
        is_equal, msg = tu.compare(obj, golden_file_path)
        assert(is_equal)
        assert(msg == '')
        
        is_equal, msg = tu.compare(obj1, golden_file_path)
        assert(not is_equal)
        msg_expected = '''\
obj is different with golden:
------golden is-----
[1, 2, 3]
------obj is--------
[1, 2]'''
        self.assertEqual(msg_expected, msg)
        
if __name__ == "__main__":
    unittest.main()

    