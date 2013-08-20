'''test_find_reference_util.py -- unittest for
find_reference_util.py
'''

import os, sys, stat
from nose.tools import eq_
from nose.tools import raises

from reshaper.util import get_cursor_with_location
from reshaper.semantic import get_cursors_add_parent
from .util import get_tu_from_text

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
    file_name = "/tmp/test_get_cursors_with_name"
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
    eq_(res, None)
    eq_(ref, [])
    
def test_parse_find_reference_args():
    '''test function get_cursors_with_name when arguments are given properly
    '''
    file_name = "/tmp/testfile"
    tmp_file = open(file_name, 'w')
    tmp_file.close()
    
    sys.argv[1:] = ['--file=/tmp/testfile', '--spelling=testspell', '-l 10', 
                 '-c 10', '--output-file=/tmp/output']    
    option = parse_find_reference_args('test_parse_find_reference_args')
    
    eq_(option.filename, '/tmp/testfile')
    eq_(option.column, 10)
    eq_(option.line, 10)
    eq_(option.spelling, 'testspell')
    eq_(option.output_file_name, '/tmp/output')
    
    sys.argv[1:] = ['--file=/tmp/testfile', '--spelling=testspell', '-l 10']    
    option = parse_find_reference_args('test_parse_find_reference_args')
    
    eq_(option.column, None)
    eq_(option.output_file_name, './test_parse_find_reference_args')
    
    os.remove(file_name)

def test_parse_find_reference_args2():
    '''test when invalid output file is given by command line
    '''
    file_name = '/tmp/testfile'
    tmp_file = open(file_name, 'w')
    tmp_file.close()
    
    invalid_output_file = '/tmp/invalid_output'
    tmp_file = open(invalid_output_file, 'w')
    tmp_file.close()
    os.chmod(invalid_output_file, not stat.S_IWUSR)
    
    sys.argv[1:] = ['--file=/tmp/testfile', '--spelling=testspell', '-l 10', 
                 '-c 10', '--output-file=/tmp/invalid_output']    
    option = parse_find_reference_args('test_parse_find_reference_args')
    
    eq_(option.output_file_name, './test_parse_find_reference_args')
    
    os.remove(file_name)
    os.remove(invalid_output_file)

@raises(SystemExit)
def test_parse_find_reference_args3():
    '''test function get_cursors_with_name when filename is not given
    '''
    sys.argv[1:] = ['--spelling=testspell', '-l 10', '-c 10']
    parse_find_reference_args('test_parse_find_reference_args') 

@raises(SystemExit)
def test_parse_find_reference_args4():
    '''test function get_cursors_with_name when filename does not exist
    '''
    sys.argv[1:] = ['--file=/tmp/not_exist', '--spelling=testspell', 
                    '-l 10', '-c 10']
    parse_find_reference_args('test_parse_find_reference_args') 
    
@raises(SystemExit)    
def test_parse_find_reference_args5():
    '''test function get_cursors_with_name when spelling is not given
    '''
    file_name = "/tmp/testfile"
    tmp_file = open(file_name, 'w')
    tmp_file.close()
    
    sys.argv[1:] = ['--file=/tmp/testfile', '-l 10', '-c 10']
    parse_find_reference_args('test_parse_find_reference_args') 
    
@raises(SystemExit)    
def test_parse_find_reference_args6():
    '''test function get_cursors_with_name when line is not given
    '''
    file_name = "/tmp/testfile"
    tmp_file = open(file_name, 'w')
    tmp_file.close()
        
    sys.argv[1:] = ['--file=/tmp/testfile', '--spelling=testspell', '-c 10']
    parse_find_reference_args('test_parse_find_reference_args') 
    