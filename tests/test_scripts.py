'''unit tests for scripts'''

from tests.util import assert_stdout, abnormal_sysexit
import extract_interface

import os, sys

_INPUT_PATH = os.path.join(os.path.dirname(__file__), 
                       'test_data', 'test_scripts.c')
_EXP_OUT = '''\
class IA
{
public:
    virtual ~IA {}
    virtual void foo() = 0;
    virtual int bar(double d) = 0;
    virtual Outer::B test_B(*Outer::B) = 0;
    virtual Outer::Inner::C test_C (*Outer::Inner::C) = 0;
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

@assert_stdout(_EXP_OUT)
def test_extract_interface():
    '''test script extract_interface 
    '''
    extract_interface.main([_INPUT_PATH, 'A']) #golbal
    extract_interface.main([_INPUT_PATH, 'Outer::D']) #in namespace
    extract_interface.main([_INPUT_PATH, 'Outer::B::D']) #in class in namespace
    
@abnormal_sysexit
def test_extract_interface_err1():
    '''test script extract_interface with invalid input:
       get class in lower namespace and cause error
    '''
    extract_interface.main([_INPUT_PATH, 'B']) 
    
@abnormal_sysexit
def test_extract_interface_err2():
    '''test script extract_interface with invalid input:
       get invalid class and cause error
    '''
    extract_interface.main([_INPUT_PATH, 'Invalid']) 
    
@abnormal_sysexit
def test_extract_interface_err3():
    '''test script extract_interface with invalid input:
       try to get Outer::B::C and cause error
    '''
    extract_interface.main([_INPUT_PATH, 'Outer::C']) 
    
@abnormal_sysexit
def test_extract_interface_err4():
    '''test script extract_interface with invalid input:
       try to get class declaration 
    '''
    extract_interface.main([_INPUT_PATH, 'Outer::Inner::B']) 