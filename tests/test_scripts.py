'''unit tests for scripts'''

from tests.util import assert_stdout, abnormal_exit, file_equals_str

import extract_interface
import find_call_chain
import find_reference
import gen_collaboration_graph
import serialize_class
import ast_dump

import os

_INPUT_PATH = os.path.join(os.path.dirname(__file__), 
                       'test_data', 'test_scripts.c')
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
      
def test_find_call_chain():
    '''test find_call_chain.py script
    '''
    input_dir_path = os.path.join(os.path.dirname(__file__), 
                             'test_data', 'call_chain')
    output_path = os.path.join(input_dir_path, 'out.txt')
    
    args = ['-f', os.path.join(input_dir_path, 'b.h'), '-s', 'TargetFunc',\
            '-d', input_dir_path, '-o', output_path,
            '-l', '4', '-c', '7']    
    find_call_chain.main(args)
    assert  file_equals_str(output_path, '''\
digraph G{
"callint()" -> "Test::TargetFunc(int)";
}
''')
    
    args = ['-f', os.path.join(input_dir_path, 'b.h'), '-s', 'TargetFunc',\
            '-d', input_dir_path, '-o', output_path,
            '-l', '6', '-c', '7']    
    find_call_chain.main(args)
    assert  file_equals_str(output_path, '''\
digraph G{
"callfloat()" -> "Test::TargetFunc(float)";
}
''')
    
    args = ['-f', os.path.join(input_dir_path, 'b.h'), '-s', 'TargetFunc',\
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
    
def test_find_reference():
    '''test find_reference.py script
    '''
    input_dir_path = os.path.join(os.path.dirname(__file__), 
                             'test_data', 'call_chain')
    output_path = os.path.join(input_dir_path, 'out.txt')
    
    args = ['-f', os.path.join(input_dir_path, 'c.h'), '-s', 'TargetFunc1',\
            '-d', input_dir_path, '-o', output_path,
            '-l', '4', '-c', '6']
    find_reference.main(args)
    assert  file_equals_str(output_path, '''
Reference of "TargetFunc1()": file : ''' + os.path.join(input_dir_path, 'c.h') \
+ ''', location 4 6 
----------------------------------------------------------------
 file : ''' + os.path.join(input_dir_path, 'c.cpp') + ''' 
Call function:foo()
line 5, column 4
----------------------------------------------------------------
 file : ''' + os.path.join(input_dir_path, 'c.h') + ''' 
class : Test
line 4, column 6
''')

    args = ['-f', os.path.join(input_dir_path, 'c.cpp'), '-s', 'TargetFunc2',\
            '-d', input_dir_path, '-o', output_path,
            '-l', '8', '-c', '5']
    find_reference.main(args)
    assert  file_equals_str(output_path, '''
Reference of "TargetFunc2()": file : ''' + os.path.join(input_dir_path, 'c.cpp') \
+ ''', location 8 5 
----------------------------------------------------------------
 file : ''' + os.path.join(input_dir_path, 'c.cpp') + ''' 
global function
line 8, column 5
----------------------------------------------------------------
 file : ''' + os.path.join(input_dir_path, 'c.cpp') + ''' 
Call function:TargetFunc3()
line 15, column 3
''')
    
    args = ['-f', os.path.join(input_dir_path, 'c.cpp'), '-s', 'TargetFunc3',\
            '-d', input_dir_path, '-o', output_path,
            '-l', '14', '-c', '7']
    find_reference.main(args)
    assert  file_equals_str(output_path, '''
Reference of "TargetFunc3()": file : ''' + os.path.join(input_dir_path, 'c.cpp') \
+ ''', location 14 7 
----------------------------------------------------------------
 file : ''' + os.path.join(input_dir_path, 'c.cpp') + ''' 
anonymouse namespace
line 14, column 7
''')
    
    args = ['-f', os.path.join(input_dir_path, 'c.cpp'), '-s', 'TargetFunc4',\
            '-d', input_dir_path, '-o', output_path,
            '-l', '20', '-c', '7']
    find_reference.main(args)
    assert  file_equals_str(output_path, '''
Reference of "TargetFunc4()": file : ''' + os.path.join(input_dir_path, 'c.cpp') \
+ ''', location 20 7 
----------------------------------------------------------------
 file : ''' + os.path.join(input_dir_path, 'c.cpp') + ''' 
namespace : Test_ns
line 20, column 7
''')


_EXP_OUT2 = '''\
digraph G {
  rankdir = LR;
  edge [fontname="Helvetica",fontsize="10",labelfontname="Helvetica",labelfontsize="10"];
  node [fontname="Helvetica",fontsize="10",shape=record];
  Node1 [label="A0",height=0.2,width=0.4,color="black", fillcolor="grey75", style="filled" fontcolor="black"];
  Node2 [label="A",height=0.2,width=0.4,color="black", fillcolor="grey75", style="filled" fontcolor="black"];
  Node1 -> Node2 [dir="back", color="midnightblue",fontsize="10",style="solid",label="<inherit>",fontname="Helvetica"];  
  Node3 [label="X",height=0.2,width=0.4,color="black", fillcolor="grey75", style="filled" fontcolor="black"];
  Node2 -> Node3 [color="midnightblue",fontsize="10",style="dashed",label="m_x" ,fontname="Helvetica"];
  Node2 -> Node3 [color="midnightblue",fontsize="10",style="dashed",label="m_x1" ,fontname="Helvetica"];
  Node2 -> Node3 [color="midnightblue",fontsize="10",style="dashed",label="m_x2" ,fontname="Helvetica"];
  Node4 [label="Y",height=0.2,width=0.4,color="black", fillcolor="grey75", style="filled" fontcolor="black"];
  Node2 -> Node4 [color="midnightblue",fontsize="10",style="dashed",label="m_y1" ,fontname="Helvetica"];
  Node2 -> Node4 [color="midnightblue",fontsize="10",style="dashed",label="m_y2" ,fontname="Helvetica"];
  Node5 [label="Other",height=0.2,width=0.4,color="black", fillcolor="grey75", style="filled" fontcolor="black"];
  Node2 -> Node5 [color="midnightblue",fontsize="10",style="dashed",label="m_other" ,fontname="Helvetica"];
  Node2 -> Node3 [color="darkorchid3",fontsize="10",style="dashed",label="X" ,fontname="Helvetica"];
  Node6 [label="Y1",height=0.2,width=0.4,color="black", fillcolor="grey75", style="filled" fontcolor="black"];
  Node2 -> Node6 [color="darkorchid3",fontsize="10",style="dashed",label="Y1" ,fontname="Helvetica"];
  Node7 [label="auto_ptr",height=0.2,width=0.4,color="black", fillcolor="grey75", style="filled" fontcolor="black"];
  Node2 -> Node7 [color="darkorchid3",fontsize="10",style="dashed",label="auto_ptr" ,fontname="Helvetica"];
  Node2 -> Node5 [color="darkorchid3",fontsize="10",style="dashed",label="f" ,fontname="Helvetica"];
  Node2 -> Node3 [color="darkorchid3",fontsize="10",style="dashed",label="m_funcx" ,fontname="Helvetica"];
  Node8 [label="Z",height=0.2,width=0.4,color="black", fillcolor="grey75", style="filled" fontcolor="black"];
  Node2 -> Node8 [color="darkorchid3",fontsize="10",style="dashed",label="m_funcz" ,fontname="Helvetica"];
}'''
@assert_stdout(_EXP_OUT2)
def test_gen_collaboration_graph():
    '''test gen_collaboration_graph.py script
    '''
    input_file = os.path.join(os.path.dirname(__file__), 
                             'test_data', 'class_relation.cpp')
    args = ['-f', input_file, '-s', 'True', 'A']
    gen_collaboration_graph.main(args)


_EXP_OUT3 = '''\
friend bool operator == (const A& a, const A& b)
{ 
          return (    
                  a.m_i == b.m_i &&    
                  a.m_i2 == b.m_i2 &&    
                  a.m_b == b.m_b &&    
                  *(a.p_int1) == *(b.p_int1) &&    
                  *(a.p_int2) == *(b.p_int2) &&    
                  *(a.p_B) == *(b.p_B) &&
                  true);
}

///serialization function for class A:
template<class Archive>
void serialize(Archive & ar, const unsigned int version)
{
    ar & BOOST_SERIALIZATION_NVP(m_i);
    ar & BOOST_SERIALIZATION_NVP(m_i2);
    ar & BOOST_SERIALIZATION_NVP(p_int1);
    ar & BOOST_SERIALIZATION_NVP(p_int2);
    ar & BOOST_SERIALIZATION_NVP(m_b);
    ar & BOOST_SERIALIZATION_NVP(p_B);       
}'''
@assert_stdout(_EXP_OUT3)
def test_serialize_class():
    '''test serialize_class.py script
    '''
    input_file = os.path.join(os.path.dirname(__file__), 
                             'test_data', 'test_serializer.cpp')
    args = [input_file, 'A']
    serialize_class._main(args)
    
def test_ast_dump():
    '''test ast_dump.py script
    '''
    input_file = os.path.join(os.path.dirname(__file__), 
                             'test_data', 'test_serializer.cpp')
    args = [input_file]
    ast_dump.main(args)
    
#test_ast_dump()


