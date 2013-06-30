'''
Created on Jun 24, 2013

@author: liangzhao
'''

import reshaper.dot_parser as dp
import operator

def calculate_set_correlation(set1, set2):
    if(len(set1)+ len(set2) ==0):
        return 1
    
    intersect = set1.intersection(set2)
    return len(intersect)*2.0/(len(set1)+len(set2))

def calculate_set_dist(set1, set2):
    return 1 - calculate_set_correlation(set1, set2)


def calc_set_inclusion_percentage(set1, set2):
    ''' calculate percentage of set1 that is included by set2
    '''
    if not set1:
        return 0
    
    intersect = set1.intersection(set2)
    return len(intersect)*1.0/len(set1)


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
        
    
    def get_all_dependings(self, node, max_level=3):
        ''' 
        get all nodes directly or indirectly depend on node
        '''
    
        return self.get_all_related(node, max_level, self.get_depending_on)
    
    def get_all_depened(self, node, max_level=100):
        ''' 
        get all nodes directly or indirectly depended by node
        '''
        return self.get_all_related(node, max_level, self.get_depended_by)
    
    def get_depended_leafs_by(self, node):
        '''
        get all leaf node depeneded by node
        '''
        all_depended = self.get_all_depened(node)
        
        return set(filter(lambda depended: depended in self.get_depended_leafs(), \
                      all_depended))
        
    def calc_depeneded_correlation(self, node, leaf_nodes):
        ''' compare all related leafs of node with leaf_nodes, 
            calculate correlation
        '''
        depened_leafs = self.get_depended_leafs_by(node)
        return calc_set_inclusion_percentage(depened_leafs,
                                                leaf_nodes)
    
    def calc_all_depended_correlation(self, leaf_nodes, 
                                      threashold = 0.6):
        ''' calculate all depended nodes's depended_correlation with 
            leaf_nodes 
        '''
        node2correlation = {}
        for node in self.depended_dict.keys():
            correlation = self.calc_depeneded_correlation(node, leaf_nodes)
            if  correlation >= threashold:
                node2correlation[node] = correlation
        
        return sorted(node2correlation.iteritems(), \
                      key=operator.itemgetter(1), reverse=True)     
        
    
    def get_all_related(self,node, max_level, relation_func):
        
        all_related = set([node])
        
        def _get_related(node, all_related, level):
            if level > max_level:
                return
            
            for depending in relation_func(node):
                if depending in all_related:
                    continue
                else:
                    all_related.add(depending)
                    _get_related(depending, all_related, level+1)
    
        _get_related(node, all_related, 0)
        all_related.remove(node)
    
        return all_related
    
    def calculate_correlation(self, node1, node2):
        dep1 = self.get_all_dependings(node1, max_level=1)
        dep2 = self.get_all_dependings(node2, max_level=1)
        
        return calculate_set_correlation(dep1, dep2)
    
   
    def get_depended_leafs(self):
        '''
        get all leaf nodes that are depended by some nodes, 
        but do not depending on any other nodes
        '''
        return [node for node in self.depending_dict \
                     if node not in self.depended_dict] 
        
    def calculate_all_correlation(self, node, threashold = 0.4):
        node2correlation = {}
        for leaf_node in self.get_depended_leafs():
            correlation = self.calculate_correlation(node, leaf_node)
            if leaf_node != node and correlation >= threashold:
                node2correlation[leaf_node] = correlation
        
        return sorted(node2correlation.iteritems(), \
                      key=operator.itemgetter(1), reverse=True)
    
    def print_all_leaf_relation(self):
        for leaf_node in self.get_depended_leafs():
            print leaf_node
            all_correlation = self.calculate_all_correlation(leaf_node)
            for node, correlation in all_correlation:
                print node, correlation
            print 
    
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
            
          
            
            
            