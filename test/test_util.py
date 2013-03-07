'''
Created on 2013-3-5

@author: liangzhao
'''

import os, pickle

def compare(obj, golden_file_path):
    '''
    if the golden file dose not exist, will generate it and return TRUE,
    otherwise it will compare the obj with the golden file.
    When return False , error message will contain difference of two obj 
    '''
    if not os.path.isfile(golden_file_path):
          golden_file = open(golden_file_path,'w')
          pickle.dump(obj, golden_file)
          return (True,'')        
        
    golden_file = open(golden_file_path,'r')
    obj_golden =  pickle.load(golden_file)
    is_equal = (obj == obj_golden)
    if is_equal:
        return (True,'')
    else: 
        msg =  'obj is different with golden:\n'
        msg += '------golden is-----\n'
        msg += str(obj_golden) + '\n'
        msg += '------obj is--------\n'
        msg += str(obj) 
        return (False,msg)
            
    
    