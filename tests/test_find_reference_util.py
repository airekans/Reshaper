'''test_find_reference_util.py -- unittest for
find_reference_util.py
'''

import os, stat
from nose.tools import eq_

from reshaper.util import get_cursor_with_location
from reshaper.semantic import get_cursors_add_parent
from .util import get_tu_from_text, redirect_stderr, abnormal_exit

from reshaper.find_reference_util import filter_cursors_by_usr
from reshaper.find_reference_util import get_cursors_with_name
from reshaper.find_reference_util import parse_find_reference_args

TEST_INPUT = """\
class TestClass
{
public:
    void TargetFunc()
    {
    }
}

namespace TestNS
{
    void TargetFunc()
    {
    }
}

void CallFunc()
{
    TestClass *pTC = new TestClass();
    pTC->TargetFunc();

    TestNS::TargetFunc();
}
"""

def test_filter_cursurs_by_usr():
    '''test function filter_cursors_by_usr
    '''
    _tu = get_tu_from_text(TEST_INPUT)
    spelling = "TargetFunc"
    target_cursor = get_cursor_with_location(_tu, spelling, 4)
    target_usr = target_cursor.get_usr()

    candidate_curs = get_cursors_add_parent(_tu, spelling)

    eq_(len(candidate_curs), 7)
    final_curs = filter_cursors_by_usr(candidate_curs, target_usr)
    eq_(len(final_curs), 2)
    eq_(final_curs[0].location.line, 4)
    eq_(final_curs[1].location.line, 19)

def test_get_cursors_with_name():
    '''test function get_cursors_with_name
    '''
    file_name = os.path.join(os.path.dirname(__file__), 
                             'test_data', 'test_find_reference_util_tmp')
    tmp_file = open(file_name, 'w')
    tmp_file.write(TEST_INPUT)
    tmp_file.close()
    
    name = "TargetFunc"
    ref = []
    get_cursors_with_name(file_name, name, ref)
    os.remove(file_name)
    eq_(len(ref), 7)
    
    ref = []
    res = get_cursors_with_name(file_name, name, ref)
    assert res is None
    eq_(ref, [])
    
def test_parse_find_refe_args_regular():
    '''test function get_cursors_with_name when command line arguments are 
    given properly
    '''
    #regular situation with all arguments properly given
    file_name = os.path.join(os.path.dirname(__file__), 
                             'test_data', 'test_find_reference_util_tmp')
    output_file = os.path.join(os.path.dirname(__file__), 
                             'test_data', 'test_find_refe_util_out_tmp')
    open(file_name, 'w').close()
    
    args = ['--file=' + file_name, '--spelling=testspell', 
            '-l', '10', '-c', '10', '--output-file=' + output_file]    
    option = parse_find_reference_args('def_output_filename', args)
    
    eq_(option.filename, file_name)
    eq_(option.column, 10)
    eq_(option.line, 10)
    eq_(option.spelling, 'testspell')
    eq_(option.output_file_name, output_file)
    
    #no output filename is given, will use default
    args = ['--file=' + file_name, '--spelling=testspell',
            '-l', '10']    
    option = parse_find_reference_args('def_output_filename', args)
    
    assert option.column is None
    eq_(option.output_file_name, './def_output_filename')
    
    os.remove(file_name)

def test_parse_find_refe_args2_inv_outfile():
    '''test if command line argument '--output-file' is invalid
    '''
    file_name = os.path.join(os.path.dirname(__file__), 
                             'test_data', 'test_find_reference_util_tmp')
    inv_outfile = os.path.join(os.path.dirname(__file__), 
                             'test_data', 'test_inv_out')
    open(file_name, 'w').close()
    open(inv_outfile, 'w').close()
    os.chmod(inv_outfile, stat.S_IRUSR)
    
    args = ['--file=' + file_name, '--spelling=testspell', '-l', 
            '10', '-c', '10', '--output-file=' + inv_outfile]    
    option = parse_find_reference_args('def_output_filename', args)
    
    eq_(option.output_file_name, './def_output_filename')
    
    os.remove(file_name)
    os.remove(inv_outfile)

@redirect_stderr
@abnormal_exit
def test_parse_find_refe_args3_no_fname():
    '''test if command line argument '--file' is not given
    '''
    args = ['--spelling=testspell', '-l', '10', '-c', '10']
    parse_find_reference_args('def_output_filename', args, 
                              'test_parse_find_refe_args3_no_fname') 

@redirect_stderr
@abnormal_exit
def test_parse_find_refe_args4_inv_fname():
    '''test if command line argument '--file' is invalid
    '''
    args = ['--file=not_exist', '--spelling=testspell', 
            '-l', '10', '-c', '10']
    parse_find_reference_args('def_output_filename', args, 
                              'test_parse_find_refe_args4_inv_fname') 

@redirect_stderr
@abnormal_exit   
def test_parse_find_refe_args5_no_spell():
    '''test if command line argument '--spelling' is not given
    '''
    file_name = os.path.join(os.path.dirname(__file__), 
                             'test_data', 'test_find_reference_util_tmp')
    open(file_name, 'w').close()
    
    args = ['--file=' + file_name, '-l', '10', '-c', '10']
    parse_find_reference_args('def_output_filename', args, 
                              'test_parse_find_refe_args5_no_spell') 

@redirect_stderr
@abnormal_exit   
def test_parse_find_refe_args6_no_line():
    '''test if command line argument '--line' is not given
    '''
    file_name = os.path.join(os.path.dirname(__file__), 
                             'test_data', 'test_find_reference_util_tmp')
    open(file_name, 'w').close()
        
    args = ['--file=' + file_name, '--spelling=testspell', '-c', '10']
    parse_find_reference_args('def_output_filename', args, 
                              'test_parse_find_refe_args6_no_line') 