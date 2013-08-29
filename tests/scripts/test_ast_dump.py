'''test ast_dump.py script'''
import ast_dump
import os, sys

def test_ast_dump():
    '''test ast_dump.py script
        output to sys.stdout is first stored in a file, then compared with
        reference file line by line
    '''
    input_file = os.path.join(os.path.dirname(__file__), 
                             'test_data', 'test_ast_dump.cpp')
    output_file = os.path.join(os.path.dirname(__file__), 
                             'test_data', 'test_ast_dump.out')
    ref_file = os.path.join(os.path.dirname(__file__), 
                             'test_data', 'test_ast_dump.ref')
    
    #redirect stdout and store it in output file
    old_stdout = sys.stdout
    redirect = open(output_file, 'w')
    sys.stdout = redirect
    
    
    args = [input_file]
    ast_dump.main(args)
    
    args = ['-l', '1', '-r', input_file]
    ast_dump.main(args)
    
    args = ['-a', '-x', input_file]
    ast_dump.main(args)
    
    sys.stdout.flush()
    sys.stdout = old_stdout
    
    #compare output file with reference file 
    out_str = open(output_file, 'r')
    out_line = out_str.readline()
    ref_str = open(ref_file, 'r')
    ref_line = ref_str.readline()
    
    while out_line and ref_line:
        if not out_line.strip().startswith(ref_line.rstrip('\n')):
            raise AssertionError
        out_line = out_str.readline()
        ref_line = ref_str.readline()
            
    out_str.close()
    ref_str.close()