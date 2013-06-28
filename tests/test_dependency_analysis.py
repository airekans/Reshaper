'''
Created on Jun 24, 2013

@author: liangzhao
'''
import unittest
import reshaper.dependency_analysis as da

class Test(unittest.TestCase):

    def test_calculate_set_dist(self):
        
        set1 = set([])
        set2 = set([])
        self.assertEqual(0, da.calculate_set_dist(set1, set2))
        
        set1 = set([1, 2, 3])
        set2 = set([1, 2, 3])
        self.assertEqual(0, da.calculate_set_dist(set1, set2))
        
        set2 = set([4, 5])
        self.assertEqual(1, da.calculate_set_dist(set1, set2))
        
        set2 = set([2, 3])
        dist1 = da.calculate_set_dist(set1, set2)
        self.assertLess(dist1, 1)
        self.assertLess(0, dist1)
        
        set2 = set([2, 4, 5])
        dist2 = da.calculate_set_dist(set1, set2)
        self.assertLess(dist1, dist2)
        self.assertLess(dist2, 1)
        
    def test_cluster(self):
        cluster = da.DependencyCluster()
        test_data = ['a', 'a1',
                     'a', 'b1',
                     'a', 'c1',
                     'b', 'c1',
                     'b', 'a1',
                     'e', 'e1',
                     'e', 'f1',
                     'c1', 'c2',
                     'e1', 'e2'
                    ]
               
        for (node, depended) in zip(test_data[0::2], test_data[1::2]):
            cluster.add_node(node, depended)
            
        self.assertEqual(set(['a1','b1','c1','a']), cluster.get_depended_by('a'))
        self.assertEqual(set(['a','b']), cluster.get_depending_on('c1'))
            
        print cluster.cluster(1)
        


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
    
    
    
    