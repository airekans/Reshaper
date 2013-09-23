'''test script extract interface'''

from tests.util import assert_stdout, abnormal_exit
import extract_interface
import os

_INPUT_PATH = os.path.join(os.path.dirname(__file__), 
                       'test_data', 'test_ext_interface.c')
_EXP_OUT1 = '''\
class IA
{
public:
    virtual ~IA {}
    virtual void foo() = 0;
    virtual int bar(double d) = 0;
    virtual B test_B(*B) = 0;
    virtual Inner::C test_C (*Inner::C) = 0;
};
class ID
{
public:
    virtual ~ID {}
    virtual void bar() = 0;
    virtual int outer_d() = 0;
};
class ID
{
public:
    virtual ~ID {}
    virtual void foo() = 0;
    virtual int outer_b_d() = 0;
};'''

@assert_stdout(_EXP_OUT1)
def test_extract_interface():
    '''test script extract_interface 
    '''
    extract_interface.main([_INPUT_PATH, 'A']) #golbal
    extract_interface.main([_INPUT_PATH, 'Outer::D']) #in namespace
    extract_interface.main([_INPUT_PATH, 'Outer::B::D']) #in class in namespace
    
@abnormal_exit
def test_extract_interface_err1():
    '''test script extract_interface with invalid input:
       get class in lower namespace and cause error
    '''
    extract_interface.main([_INPUT_PATH, 'B']) 
    
@abnormal_exit
def test_extract_interface_err2():
    '''test script extract_interface with invalid input:
       get invalid class and cause error
    '''
    extract_interface.main([_INPUT_PATH, 'Invalid']) 
    
@abnormal_exit
def test_extract_interface_err3():
    '''test script extract_interface with invalid input:
       try to get Outer::B::C and cause error
    '''
    extract_interface.main([_INPUT_PATH, 'Outer::C']) 
    
@abnormal_exit
def test_extract_interface_err4():
    '''test script extract_interface with invalid input:
       try to get class declaration 
    '''
    extract_interface.main([_INPUT_PATH, 'Outer::Inner::B']) 