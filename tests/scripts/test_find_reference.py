'''test find_reference.py'''

from tests.util import file_equals_str
import find_reference
import os



def test_find_reference():
    '''test find_reference.py script
    '''
    input_dir_path = os.path.join(os.path.dirname(__file__), 
                             'test_data', 'call_chain')
    output_path = os.path.join(input_dir_path, 'out.txt')
    
    args = ['-f', os.path.join(input_dir_path, 'c.h'), '-s', 'TargetFunc1', \
            '-d', input_dir_path, '-o', output_path,
            '-l', '4', '-c', '6']
    find_reference.main(args)
    assert  file_equals_str(output_path, '''
Reference of "TargetFunc1()": file : ''' + os.path.join(input_dir_path, 'c.h') \
+ ''', location 4 6 
----------------------------------------------------------------
 file : ''' + os.path.join(input_dir_path, 'c.cpp') + ''' 
Call function:foo()
line 5, column 4
----------------------------------------------------------------
 file : ''' + os.path.join(input_dir_path, 'c.h') + ''' 
class : Test
line 4, column 6
''')

    args = ['-f', os.path.join(input_dir_path, 'c.cpp'), '-s', 'TargetFunc2', \
            '-d', input_dir_path, '-o', output_path,
            '-l', '8', '-c', '5']
    find_reference.main(args)
    assert  file_equals_str(output_path, '''
Reference of "TargetFunc2()": file : ''' + \
os.path.join(input_dir_path, 'c.cpp') + ''', location 8 5 
----------------------------------------------------------------
 file : ''' + os.path.join(input_dir_path, 'c.cpp') + ''' 
global function
line 8, column 5
----------------------------------------------------------------
 file : ''' + os.path.join(input_dir_path, 'c.cpp') + ''' 
Call function:TargetFunc3()
line 15, column 3
''')
    
    args = ['-f', os.path.join(input_dir_path, 'c.cpp'), '-s', 'TargetFunc3', \
            '-d', input_dir_path, '-o', output_path,
            '-l', '14', '-c', '7']
    find_reference.main(args)
    assert  file_equals_str(output_path, '''
Reference of "TargetFunc3()": file : ''' + \
os.path.join(input_dir_path, 'c.cpp') + ''', location 14 7 
----------------------------------------------------------------
 file : ''' + os.path.join(input_dir_path, 'c.cpp') + ''' 
anonymouse namespace
line 14, column 7
''')
    
    args = ['-f', os.path.join(input_dir_path, 'c.cpp'), '-s', 'TargetFunc4', \
            '-d', input_dir_path, '-o', output_path,
            '-l', '20', '-c', '7']
    find_reference.main(args)
    assert  file_equals_str(output_path, '''
Reference of "TargetFunc4()": file : ''' \
+ os.path.join(input_dir_path, 'c.cpp') + ''', location 20 7 
----------------------------------------------------------------
 file : ''' + os.path.join(input_dir_path, 'c.cpp') + ''' 
namespace : Test_ns
line 20, column 7
''')