'''
Created on Sep 16, 2013

@author: liangzhao
'''
import unittest, os
import gen_collaboration_graph as gcg

_INPUT_PATH = os.path.join(os.path.dirname(__file__), 
                       '../test_data', 'class_relation.h')


class Test(unittest.TestCase):
    
    def test_gen_class_relationship(self):
        ''' test generate class external relationship graph'''
        output_path = os.path.join(os.path.dirname(__file__), 
                       'test_data', 'class_relation.h.png')
        
        argv = ['-f', _INPUT_PATH,  'A', '-o', output_path] 
        gcg.main(argv)
        
           
        
    def test_gen_internal_relationship(self):
        ''' test generate class internal relationship graph'''
        output_path = os.path.join(os.path.dirname(__file__), 
                       'test_data', 'class_internal_relation.h.png')
        argv = ['-f', _INPUT_PATH,  'A', '-o', output_path, '-i'] 
        gcg.main(argv)     
        
    

if __name__ == "__main__":
    unittest.main()
    