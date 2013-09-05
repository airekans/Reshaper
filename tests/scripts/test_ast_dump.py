'''test ast_dump.py script'''
import ast_dump
import os, StringIO
from tests.util import RedirectStdStreams

def test_ast_dump():
    '''test ast_dump.py script
        output to sys.stdout is first stored in a file, then compared with
        reference file line by line
    '''
    input_file = os.path.join(os.path.dirname(__file__), 
                             'test_data', 'test_ast_dump.cpp')
    ref_file = os.path.join(os.path.dirname(__file__), 
                             'test_data', 'test_ast_dump.ref')
    
    out_str = StringIO.StringIO()
    ref_str = open(ref_file, 'r')
    
    #redirect stdout and store it in output file    
    with RedirectStdStreams(stdout=out_str):
        args = [input_file]
        ast_dump.main(args)
    
        args = ['-l', '1', '-r', input_file]
        ast_dump.main(args)
    
        args = ['-a', '-x', input_file]
        ast_dump.main(args)
    
    #compare output file with reference file 
    for out_line, ref_line in zip(out_str, ref_str):
        assert(out_line.strip().startswith(ref_line.rstrip('\n')))
            
    out_str.close()
    ref_str.close()