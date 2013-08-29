'''test gen_collaboration_graph.py script'''
from tests.util import assert_stdout
import gen_collaboration_graph
import os


_EXP_OUT = '''\
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
@assert_stdout(_EXP_OUT)
def test_gen_collaboration_graph():
    '''test gen_collaboration_graph.py script
    '''
    input_file = os.path.join(os.path.dirname(__file__), 
                             'test_data', 'test_gen_graph.cpp')
    args = ['-f', input_file, '-s', 'True', 'A']
    gen_collaboration_graph.main(args)
    