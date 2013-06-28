'''
Created on Jun 24, 2013

@author: liangzhao
'''

from cluster import HierarchicalClustering

def calculate_set_dist(set1, set2):
    if(len(set1)+ len(set2) ==0):
        return 0
    
    intersect = set1.intersection(set2)
    return 1 - len(intersect)*2.0/(len(set1)+len(set2))


class DependencyCluster(object):
    '''
    dependency graph
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.depended_dict = {}
        self.depending_dict = {}
        self.all_nodes = set([])
        
    def __add_value(self, key, val, dict):
        
        try:
            dict[key].add(val)
        except KeyError:
            dict[key] = set([val])  
    
    def add_node(self, node, depeneded_node): 
        '''
        add node
        '''
        self.__add_value(node, depeneded_node, self.depended_dict)  
        self.__add_value(node, node, self.depended_dict)  
        self.__add_value(depeneded_node, node, self.depending_dict) 
        self.all_nodes.add(node)
        self.all_nodes.add(depeneded_node) 
        
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
        
    
    
    def calculate_dist(self, node1, node2):
        '''
        calculate distance of two nodes
        '''
        db1 = self.get_depended_by(node1)
        db2 = self.get_depended_by(node2)
        db_dist = calculate_set_dist(db1, db2)
        
        do1 = self.get_depending_on(node1)
        do2 = self.get_depending_on(node2)
        do_dist = calculate_set_dist(do1, do2)
        
        dist = db_dist + do_dist
        print node1, node2, dist
        
        return dist
         
        
    def cluster(self, threashold):  
        all_nodes = list(self.all_nodes)
        cl = HierarchicalClustering(all_nodes, self.calculate_dist)
        return cl.getlevel(threashold)  
    
    
    
    
    
    
    
    