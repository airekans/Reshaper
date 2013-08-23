from tests.util import  AssertStdout
from nose.tools import raises
import extract_interface

import os
    
_INPUT_TEXT = '''\
class D
{
    D();
    virtual ~D();
    void foo();
    int global_d();
};

namespace Outer{
    namespace Inner{
        class C
        {
            C();
            virtual ~C();
            void foo();
            int bar(double d);
        };
        class D
        {
            D();
            virtual ~D();
            void foo();
            int outer_inner_d();
        };
    }
    
    class B
    {
        class D
        {
            D();
            virtual ~D();
            void foo();
            int outer_b_d();
        };
        B();
        virtual ~B();
        void foo();
        int bar(double d);
        Inner::C test_C(*Inner::C);
    };
    
    class D
    {
        D();
        virtual ~D();
        void bar();
        int outer_d();
    };
}

class A
{
public:
    A();
    virtual ~A();
    void foo();
    int bar(double d);
    Outer::B test_B(*Outer::B);
    Outer::Inner::C test_C (*Outer::Inner::C);
};'''
    
input_path = os.path.join(os.path.dirname(__file__), 
                       'test_data', 'test_scripts.c')
tmpf = open(input_path, 'w')
tmpf.write(_INPUT_TEXT)
tmpf.close()

_EXP_OUT='''\
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

@AssertStdout(_EXP_OUT)
def test_extract_interface():
    extract_interface.main([input_path, 'A']) #golbal
    extract_interface.main([input_path, 'Outer::D']) #in namespace
    extract_interface.main([input_path, 'Outer::B::D']) #in class in namespace
    
@raises(SystemExit)
def test_extract_interface_err1():
    extract_interface.main([input_path, 'B']) #get class in lower namespace
    
@raises(SystemExit)
def test_extract_interface_err2():
    extract_interface.main([input_path, 'Invalid']) #get invalid class
    
@raises(SystemExit)
def test_extract_interface_err3():
    extract_interface.main([input_path, 'Outer::C']) #try to get Outer::B::C
        
            
        