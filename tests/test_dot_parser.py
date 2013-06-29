'''
Created on Jun 29, 2013

@author: liangzhao
'''
import unittest
import reshaper.dot_parser as dp


class Test(unittest.TestCase):

    def test_dot_parse(self):
        node_line =  '    Node1 [label="SetUI",height=0.2];'
        (node_name, node_label) = dp.parse_node_line(node_line)
        self.assertEqual('Node1', node_name)
        self.assertEqual('SetUI', node_label)
        
        edge_line = '    Node3 -> Node4 [label=""]' 
        self.assertEqual((None,None), dp.parse_node_line(edge_line))
        
        
        self.assertEqual((None,None), dp.parse_edge_line(node_line))
        self.assertEqual(('Node3','Node4'), dp.parse_edge_line(edge_line))
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()