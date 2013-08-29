'''test script find_call_chain.py'''

import find_call_chain
import os
from tests.util import file_equals_str


def test_find_call_chain():
    '''test find_call_chain.py script
    '''
    input_dir_path = os.path.join(os.path.dirname(__file__), 
                             'test_data', 'call_chain')
    output_path = os.path.join(input_dir_path, 'out.txt')
    
    args = ['-f', os.path.join(input_dir_path, 'b.h'), '-s', 'TargetFunc', \
            '-d', input_dir_path, '-o', output_path,
            '-l', '4', '-c', '7']    
    find_call_chain.main(args)
    assert  file_equals_str(output_path, '''\
digraph G{
"callint()" -> "Test::TargetFunc(int)";
}
''')
    
    args = ['-f', os.path.join(input_dir_path, 'b.h'), '-s', 'TargetFunc', \
            '-d', input_dir_path, '-o', output_path,
            '-l', '6', '-c', '7']    
    find_call_chain.main(args)
    assert  file_equals_str(output_path, '''\
digraph G{
"callfloat()" -> "Test::TargetFunc(float)";
}
''')
    
    args = ['-f', os.path.join(input_dir_path, 'b.h'), '-s', 'TargetFunc', \
            '-d', input_dir_path, '-o', output_path,
            '-l', '12', '-c', '7']    
    find_call_chain.main(args)
    assert  file_equals_str(output_path, '''\
digraph G{
"bar()" -> "Test_ns::TargetFunc(int)";
"foo()" -> "bar()";
"fooo()" -> "foo()";
}
''')