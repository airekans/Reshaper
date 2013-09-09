'''test find_reference.py'''

from tests.util import assert_file_content
import find_reference
import os


INPUT_DIR_PATH = os.path.join(os.path.dirname(__file__), 
                             'test_data', 'call_chain')
OUTPUT_PATH = os.path.join(INPUT_DIR_PATH, 'out.txt')


def test_find_reference1_cls_method():
    '''test find_reference.py script to find reference of class method
    '''    
    args = ['-f', os.path.join(INPUT_DIR_PATH, 'c.h'), '-s', 'TargetFunc1', \
            '-d', INPUT_DIR_PATH, '-o', OUTPUT_PATH,
            '-l', '4', '-c', '6']
    find_reference.main(args)
    assert_file_content('''
Reference of "TargetFunc1()": file : ''' + os.path.join(INPUT_DIR_PATH, 'c.h') \
+ ''', location 4 6 
----------------------------------------------------------------
 file : ''' + os.path.join(INPUT_DIR_PATH, 'c.cpp') + ''' 
Call function:foo()
line 5, column 4
----------------------------------------------------------------
 file : ''' + os.path.join(INPUT_DIR_PATH, 'c.h') + ''' 
class : Test
line 4, column 6
''', OUTPUT_PATH)

def test_find_reference2_glb_func():
    '''test find_reference.py script to find reference of global function
    '''    
    args = ['-f', os.path.join(INPUT_DIR_PATH, 'c.cpp'), '-s', 'TargetFunc2', \
            '-d', INPUT_DIR_PATH, '-o', OUTPUT_PATH,
            '-l', '8', '-c', '5']
    find_reference.main(args)
    assert_file_content('''
Reference of "TargetFunc2()": file : ''' + \
os.path.join(INPUT_DIR_PATH, 'c.cpp') + ''', location 8 5 
----------------------------------------------------------------
 file : ''' + os.path.join(INPUT_DIR_PATH, 'c.cpp') + ''' 
global function
line 8, column 5
----------------------------------------------------------------
 file : ''' + os.path.join(INPUT_DIR_PATH, 'c.cpp') + ''' 
Call function:TargetFunc3()
line 15, column 3
''', OUTPUT_PATH)
    
def test_find_reference3_ano_ns():
    '''test find_reference.py script to find reference of function in anonymous namespace
    '''    
    args = ['-f', os.path.join(INPUT_DIR_PATH, 'c.cpp'), '-s', 'TargetFunc3', \
            '-d', INPUT_DIR_PATH, '-o', OUTPUT_PATH,
            '-l', '14', '-c', '7']
    find_reference.main(args)
    assert_file_content('''
Reference of "TargetFunc3()": file : ''' + \
os.path.join(INPUT_DIR_PATH, 'c.cpp') + ''', location 14 7 
----------------------------------------------------------------
 file : ''' + os.path.join(INPUT_DIR_PATH, 'c.cpp') + ''' 
anonymouse namespace
line 14, column 7
''', OUTPUT_PATH)

def test_find_reference4_ns_func():
    '''test find_reference.py script to find reference of function in namespace
    '''    
    args = ['-f', os.path.join(INPUT_DIR_PATH, 'c.cpp'), '-s', 'TargetFunc4', \
            '-d', INPUT_DIR_PATH, '-o', OUTPUT_PATH,
            '-l', '20', '-c', '7']
    find_reference.main(args)
    assert_file_content('''
Reference of "TargetFunc4()": file : ''' \
+ os.path.join(INPUT_DIR_PATH, 'c.cpp') + ''', location 20 7 
----------------------------------------------------------------
 file : ''' + os.path.join(INPUT_DIR_PATH, 'c.cpp') + ''' 
namespace : Test_ns
line 20, column 7
''', OUTPUT_PATH)