from reshaper.extract import extract_interface
from reshaper.util import get_cursor
from nose.tools import eq_, with_setup
from clang.cindex import TranslationUnit
import os

INPUT_DIR = os.path.join(os.path.dirname(__file__), 'test_data')

def test_extract_interface():
    source = os.path.join(INPUT_DIR, 'class.cpp')
    tu = TranslationUnit.from_source(source, ['-std=c++11'])

    class_cursor = get_cursor(tu, 'A')
    assert(class_cursor is not None)

    # check default behavior
    expected_interface = \
"""class IA
{
public:
    virtual ~IA {}
    virtual void foo() = 0;
    virtual int bar(double d) = 0;
    virtual double fun_definition(float f, char* c) = 0;
    virtual TestStruct result_test_fun(TestStruct*) = 0;
    virtual double (*return_fun_fun(int, double))(int, double) = 0;
    virtual double fun_with_default_args(const int i = 10) = 0;
    virtual void virutal_fun(const double d) = 0;
    virtual void pure_virtual_fun(const int i) = 0;
};"""

    interface_printer = extract_interface(class_cursor)
    eq_(expected_interface, interface_printer.get_definition())

    # check selecting some methods to extract
    interface_printer = extract_interface(class_cursor, None)
    eq_(expected_interface, interface_printer.get_definition())

    expected_interface = \
"""class IA
{
public:
    virtual ~IA {}
};"""

    interface_printer = extract_interface(class_cursor, [])
    eq_(expected_interface, interface_printer.get_definition())

    interface_printer = extract_interface(class_cursor, ['', 'nonexist_fun'])
    eq_(expected_interface, interface_printer.get_definition())


    expected_interface = \
"""class IA
{
public:
    virtual ~IA {}
    virtual void foo() = 0;
};"""
    
    interface_printer = extract_interface(class_cursor, ['foo'])
    eq_(expected_interface, interface_printer.get_definition())
    

    expected_interface = \
"""class IA
{
public:
    virtual ~IA {}
    virtual void foo() = 0;
    virtual double (*return_fun_fun(int, double))(int, double) = 0;
};"""
    
    interface_printer = extract_interface(class_cursor, ['foo', 'return_fun_fun'])
    eq_(expected_interface, interface_printer.get_definition())

    # check prefix argument
    expected_interface = \
"""class InterfaceA
{
public:
    virtual ~InterfaceA {}
    virtual void foo() = 0;
};"""
    
    interface_printer = extract_interface(class_cursor, ['foo'], prefix = 'Interface')
    eq_(expected_interface, interface_printer.get_definition())
