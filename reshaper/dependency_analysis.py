'''
Created on Jun 24, 2013

@author: liangzhao
'''

import reshaper.dot_parser as dp

def calculate_set_correlation(set1, set2):
    if(len(set1)+ len(set2) ==0):
        return 1
    
    intersect = set1.intersection(set2)
    return len(intersect)*2.0/(len(set1)+len(set2))

def calculate_set_dist(set1, set2):
    return 1 - calculate_set_correlation(set1, set2)

class DependencyAnalyzer(object):
    '''
    dependency graph
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.depended_dict = {}
        self.depending_dict = {}
        
    def __add_value(self, key, val, dict):
        
        try:
            dict[key].add(val)
        except KeyError:
            dict[key] = set([val])  
    
    def add_denpendency(self, node, depeneded_node): 
        '''
        add node
        '''
        self.__add_value(node, depeneded_node, self.depended_dict)  
        self.__add_value(node, node, self.depended_dict)  
        self.__add_value(depeneded_node, node, self.depending_dict) 
        
    def get_depended_by(self, node):
        '''
        Get nodes depended by node
        '''
        try:
            return self.depended_dict[node]
        except KeyError:
            return set([node])
        
        
    def get_depending_on(self, node):
        '''
        Get nodes that are depending on node
        '''
        try:
            return self.depending_dict[node]
        except KeyError:
            return set([])
        
    
    def get_all_dependings(self, node):
        ''' 
        get all nodes directly or indirectly depend on node
        '''
        all_dependings = set([node])
        
        def _get_dependings(node, all_dependings):
            for depending in self.get_depending_on(node):
                if depending in all_dependings:
                    continue
                else:
                    all_dependings.add(depending)
                    _get_dependings(depending, all_dependings)
    
        _get_dependings(node, all_dependings)
        all_dependings.remove(node)
    
        return all_dependings
    
    def calculate_correlation(self, node1, node2):
        dep1 = self.get_all_dependings(node1)
        dep2 = self.get_all_dependings(node2)
        
        return calculate_set_correlation(dep1, dep2)
    
    def get_depended_leafs(self):
        '''
        get all leaf nodes that are depended by some nodes, 
        but do not depending on any other nodes
        '''
        return [node for node in self.depending_dict \
                     if node not in self.depended_dict] 
        
    def calculate_all_correlation(self, node):
        pass
    
class ClsMemberCorrelationAnalyzer(object):
    
    def __init__(self):
        self._analyzer = DependencyAnalyzer()
    
    def load_dot_file(self, filepath):
        f = open(filepath,'r')
        if not f:
            raise Exception('Failed to load %s' % filepath)
            
        name2label = {}
        for line in f:
            (name, label) = dp.parse_node_line(line)
            if name:
                name2label[name] = label
                continue
            
            (nodename1, nodename2) = dp.parse_edge_line(line)
            if nodename1:
                node1 = name2label[nodename1]
                node2 = name2label[nodename2]
                self._analyzer.add_denpendency(node1, node2)
            
            
    def get_analyzer(self):
        return self._analyzer  
            
          
            
            
            