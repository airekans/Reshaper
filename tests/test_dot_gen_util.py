'''
Created on May 30, 2013

@author: liangzhao
'''
import unittest, os
from reshaper.dot_gen_util import DotGenertor, gen_class_collaboration_graph
from reshaper.ast import get_tu

#the test result string is long, so ignore this warning
#pylint: disable-msg=C0301

class Test(unittest.TestCase):
    def setUp(self):
        self._dot_gen = DotGenertor()

    def test_empty_graph(self):
        dot = self._dot_gen.get_dot_str()
        expected_dot = \
'''
digraph 
{
  // INTERACTIVE_SVG=YES
  edge [fontname="Helvetica",fontsize="10",labelfontname="Helvetica",labelfontsize="10"];
  node [fontname="Helvetica",fontsize="10",shape=record];
}'''
        self.assertMultiLineEqual(expected_dot, dot)
        
    def test_class_relation_graph(self):
        ''' test DotGenertor'''
        self._dot_gen.add_inherit_class('A0', 'A1')
        self._dot_gen.add_inherit_class('A0', 'A11')
        
        self._dot_gen.add_composite_class('A1', 'm_b', 'B1')
        self._dot_gen.add_composite_class('A0', 'm_c', 'C')

        self._dot_gen.add_callee_class('B', 'func0','C')
        self._dot_gen.add_callee_class('C', 'func1','A1')
        self._dot_gen.add_callee_class('A1', 'func','B1')
        self._dot_gen.add_callee_class('A1', 'func1','B0')
        
        dot = self._dot_gen.get_dot_str()
        
        expected_dot = \
'''
digraph 
{
  // INTERACTIVE_SVG=YES
  edge [fontname="Helvetica",fontsize="10",labelfontname="Helvetica",labelfontsize="10"];
  node [fontname="Helvetica",fontsize="10",shape=record];
  Node1 [label="A0",height=0.2,width=0.4,color="black", fillcolor="grey75", style="filled" fontcolor="black"];
  Node2 [label="A1",height=0.2,width=0.4,color="black", fillcolor="grey75", style="filled" fontcolor="black"];
  Node1 -> Node2 [dir="back", color="midnightblue",fontsize="10",style="solid",label="<inherit>",fontname="Helvetica"];  
  Node3 [label="A11",height=0.2,width=0.4,color="black", fillcolor="grey75", style="filled" fontcolor="black"];
  Node1 -> Node3 [dir="back", color="midnightblue",fontsize="10",style="solid",label="<inherit>",fontname="Helvetica"];  
  Node4 [label="B1",height=0.2,width=0.4,color="black", fillcolor="grey75", style="filled" fontcolor="black"];
  Node2 -> Node4 [color="midnightblue",fontsize="10",style="dashed",label="m_b" ,fontname="Helvetica"];
  Node5 [label="C",height=0.2,width=0.4,color="black", fillcolor="grey75", style="filled" fontcolor="black"];
  Node1 -> Node5 [color="midnightblue",fontsize="10",style="dashed",label="m_c" ,fontname="Helvetica"];
  Node6 [label="B",height=0.2,width=0.4,color="black", fillcolor="grey75", style="filled" fontcolor="black"];
  Node6 -> Node5 [color="darkorchid3",fontsize="10",style="dashed",label="func0" ,fontname="Helvetica"];
  Node5 -> Node2 [color="darkorchid3",fontsize="10",style="dashed",label="func1" ,fontname="Helvetica"];
  Node2 -> Node4 [color="darkorchid3",fontsize="10",style="dashed",label="func" ,fontname="Helvetica"];
  Node7 [label="B0",height=0.2,width=0.4,color="black", fillcolor="grey75", style="filled" fontcolor="black"];
  Node2 -> Node7 [color="darkorchid3",fontsize="10",style="dashed",label="func1" ,fontname="Helvetica"];
}'''
        
        self.assertEqual(expected_dot, dot, dot)
        
        
    def test_gen_class_collaboration_graph(self):
        ''' test gen_class_collaboration_graph'''
        src_path = os.path.join(os.path.dirname(__file__),
                                'test_data','class_relation.cpp') 
        _tu = get_tu(src_path)
        
        dot_str = gen_class_collaboration_graph(_tu, 'A')
        print dot_str
        
if __name__ == "__main__":
    unittest.main()
    