'''
Created on Jun 29, 2013

@author: liangzhao
'''
import re

def parse_node_line(line):
    ''' 
    parse the line that contain node definition
    '''
    node_line_re = re.compile(r'^\s+(?P<name>\w+) \[label="(?P<label>\w+)"')
    match  = node_line_re.search(line)
    if not match:
        return (None, None)
    else:
        return match.group('name'), match.group('label')
    
def parse_edge_line(line):
    ''' 
    parse the line that contain edge definition
    '''   
    edge_line_re = re.compile(r'^\s+(?P<node1>\w+) -> (?P<node2>\w+)')
    
    match  = edge_line_re.search(line)
    if not match:
        return (None, None)
    else:
        return match.group('node1'), match.group('node2')
    
    
    
    
    