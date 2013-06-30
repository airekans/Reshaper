'''
Created on Jun 24, 2013

@author: liangzhao
'''
import unittest, os
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
        analyzer = da.DependencyAnalyzer()
        test_data = ['a', 'a1',
                     'a', 'b1',
                     'a', 'c1',
                     'b', 'c1',
                     'b', 'a1',
                     'e', 'e1',
                     'e', 'f1',
                     'c1', 'c2',
                     'e1', 'e2',
                     'e1', 'f2',
                     'c1', 'e1',
                     'c1', 'b',
                     'g1', 'g2',
                     'g1','c2'
                    ]
               
        for (node, depended) in zip(test_data[0::2], test_data[1::2]):
            analyzer.add_denpendency(node, depended)
            
        self.assertEqual(set(['a1','b1','c1']), 
                         analyzer.get_depended_by('a'))
        self.assertEqual(set(['a','b']), 
                         analyzer.get_depending_on('c1'))
        self.assertEqual(set(['a','b','e','c1','e1']), 
                         analyzer.get_all_dependings('e2'))
        self.assertEqual(set(['a','b','e','c1','e1']), 
                         analyzer.get_all_dependings('f2'))
        
        self.assertEqual(1, analyzer.calculate_correlation('e2', 'f2'))
        self.assertEqual(0, analyzer.calculate_correlation('g2', 'f2'))
        
        self.assertAlmostEqual(0.2857142857, 
                               analyzer.calculate_correlation('c2', 'f2'))
        
        self.assertEqual(set(['f1', 'f2', 'g2', 'a1', 'b1', 'c2', 'e2']), 
                         set(analyzer.get_depended_leafs()))
        
        self.assertAlmostEqual([('c2', 0.8571428571428571),
                                ('b1', 0.5)], 
                               analyzer.calculate_all_correlation('a1'))
        
        expected_leafs = set(['f2', 'a1', 'b1', 'c2', 'e2'])
        self.assertEqual(expected_leafs, 
                         analyzer.get_depended_leafs_by('a'))
        
        self.assertEqual(1, 
                         analyzer.calc_depeneded_correlation('a',
                                                    expected_leafs))
        
        expected_leafs.add('g2')
        self.assertEqual(1, 
                         analyzer.calc_depeneded_correlation('a',
                                                    expected_leafs))
    
        expected_leafs.remove('f2')
        self.assertEqual(0.8, 
                         analyzer.calc_depeneded_correlation('a',
                                                    expected_leafs))
        
    def test_ClsMemberCorrelationAnalyzer(self):  
        TEST_FILE = os.path.join(os.path.dirname(__file__),
                                     'test_data','layergroupmodel.gv')
        
        cmca = da.ClsMemberCorrelationAnalyzer()
        cmca.load_dot_file(TEST_FILE)
        analyzer = cmca.get_analyzer()
        self.assertEqual(set(['CleanUpData', 'OnGDSEvent', 'ProcessGDSText', 'CleanDefText', 'IsDefctModel', 'Close']), 
                         analyzer.get_all_dependings('m_defect'))
        self.assertAlmostEqual(0.5, 
                         analyzer.calculate_correlation('m_defect', 'm_selectedDefectID'))
        
        self.assertAlmostEqual(0.44444444, 
                         analyzer.calculate_correlation('m_defect', 'm_defText'))
        self.assertEqual(0, 
                         analyzer.calculate_correlation('m_defect', 'm_fetchCellPolygonLevel'))
        
        member_group = set(['m_pGDSMask_Setting',
                            'm_defPrepared',
                            'm_defLayer',
                            'm_def',
                            'm_defText',
                            'm_defmarker_filter',
                            'm_subjobid',
                            'm_defect',
                            'm_selectedDefectID'
                            ])
        for (depending, correlation) in \
                analyzer.calc_all_depended_correlation(member_group, 0.4):
            print (depending, correlation) 
            
        print analyzer.get_depended_leafs_by('CleanDefs')
            
#     def test_ClsMemberCorrelationAnalyzer1(self):  
#         TEST_FILE = os.path.join(os.path.dirname(__file__),
#                                      'test_data','layergroupmodel.gv ')
#         
#         cmca = da.ClsMemberCorrelationAnalyzer()
#         cmca.load_dot_file(TEST_FILE)
#         analyzer = cmca.get_analyzer()
#         analyzer.print_all_leaf_relation()
        
        
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
    
    
    
    