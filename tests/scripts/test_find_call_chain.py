'''test script find_call_chain.py'''

import find_call_chain
import os
from tests.util import assert_file_content


def test_find_call_chain():
    '''test find_call_chain.py script
    '''
    INPUT_DIR_PATH = os.path.join(os.path.dirname(__file__), 
                             'test_data', 'call_chain')
    OUTPUT_PATH = os.path.join(INPUT_DIR_PATH, 'out.txt')
    
    args = ['-f', os.path.join(INPUT_DIR_PATH, 'b.h'), '-s', 'TargetFunc', \
            '-d', INPUT_DIR_PATH, '-o', OUTPUT_PATH,
            '-l', '4', '-c', '7']    
    find_call_chain.main(args)
    assert  assert_file_content(OUTPUT_PATH, '''\
digraph G{
"callint()" -> "Test::TargetFunc(int)";
}
''')
    
    args = ['-f', os.path.join(INPUT_DIR_PATH, 'b.h'), '-s', 'TargetFunc', \
            '-d', INPUT_DIR_PATH, '-o', OUTPUT_PATH,
            '-l', '6', '-c', '7']    
    find_call_chain.main(args)
    assert  assert_file_content(OUTPUT_PATH, '''\
digraph G{
"callfloat()" -> "Test::TargetFunc(float)";
}
''')
    
    args = ['-f', os.path.join(INPUT_DIR_PATH, 'b.h'), '-s', 'TargetFunc', \
            '-d', INPUT_DIR_PATH, '-o', OUTPUT_PATH,
            '-l', '12', '-c', '7']    
    find_call_chain.main(args)
    assert  assert_file_content(OUTPUT_PATH, '''\
digraph G{
"bar()" -> "Test_ns::TargetFunc(int)";
"foo()" -> "bar()";
"fooo()" -> "foo()";
}
''')