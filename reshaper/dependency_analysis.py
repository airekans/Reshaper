'''
Created on Jun 24, 2013

@author: liangzhao
'''


def calculate_set_dist(set1, set2):
    if(len(set1)+ len(set2) ==0):
        return 0
    
    intersect = set1.intersection(set2)
    return 1 - len(intersect)*2.0/(len(set1)+len(set2))


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
    
    
    
    