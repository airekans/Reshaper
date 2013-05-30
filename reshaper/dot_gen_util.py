'''
Created on May 30, 2013

@author: liangzhao
'''

from jinja2 import Template
import header_util as hu 
import semantic as sem

NODE_TEMPLATE = \
'''
  {{node}} [label="{{label}}",height=0.2,width=0.4,color="black", fillcolor="grey75", style="filled" fontcolor="black"];
'''

INHERIT_TEMPLATE = \
'''
  {{base}} -> {{child}} [dir="back", color="midnightblue",fontsize="10",style="solid",label="<inherit>",fontname="Helvetica"];  
'''

COMPOSITE_TEMPLATE = \
'''
  {{cls}} -> {{member_cls}} [color="midnightblue",fontsize="10",style="dashed",label="{{member}}" ,fontname="Helvetica"];
'''

CALLEE_TEMPLATE = \
'''
  {{caller_cls}} -> {{callee_cls}} [color="darkorchid3",fontsize="10",style="dashed",label="{{callee}}" ,fontname="Helvetica"];
'''


class DotGenertor(object):
    def __init__(self):
        self._label2node = {}
        self._dot_str = ''
        
    def _add_node(self, label):
        if label in self._label2node:
            return
        
        node = 'Node%d' % (len(self._label2node)+1)                       
        
        self._label2node[label] = node
        
        template = Template(NODE_TEMPLATE)
                
        self._dot_str += template.render(label=label, node = node)  
    
    def add_inherit_class(self, base_cls_name, child_cls_name):
        self._add_node(base_cls_name)
        self._add_node(child_cls_name)
        
        template = Template(INHERIT_TEMPLATE)
        base_node = self._label2node[base_cls_name]
        child_node = self._label2node[child_cls_name]
        
        self._dot_str += template.render(child=child_node, \
                                         base=base_node)
        
    def add_composite_class(self, cls_name, member_name, member_cls_name):
        self._add_node(cls_name)
        self._add_node(member_cls_name)
        
        template = Template(COMPOSITE_TEMPLATE)
        cls_node = self._label2node[cls_name]
        member_cls_node = self._label2node[member_cls_name]

        self._dot_str += template.render(cls=cls_node, \
                                         member_cls=member_cls_node,
                                         member=member_name)
    
    def add_callee_class(self, cls_name, callee_name, callee_cls_name):
        self._add_node(cls_name)
        self._add_node(callee_cls_name)
        
        template = Template(CALLEE_TEMPLATE)
        cls_node = self._label2node[cls_name]
        callee_cls_node = self._label2node[callee_cls_name]

        self._dot_str += template.render(caller_cls=cls_node, \
                                         callee_cls=callee_cls_node,
                                         callee=callee_name)
    
    def get_dot_str(self):
        
        head = \
'''
digraph 
{
  // INTERACTIVE_SVG=YES
  edge [fontname="Helvetica",fontsize="10",labelfontname="Helvetica",labelfontsize="10"];
  node [fontname="Helvetica",fontsize="10",shape=record];''' 
        
        tail = '\n}'
        return head  + self._dot_str + tail



def gen_class_collaboration_graph(_tu, class_names, source_dir= None):
    dot_gen = DotGenertor()
    cls_cursors = hu.get_classes_with_names(_tu, class_names)
    
    if source_dir:
        keep_func = lambda c : sem.is_cursor_in_dir(c, source_dir)
    else:
        keep_func = lambda c: True

    
    for cls_cursor in cls_cursors:
        member_with_def_classes = hu.get_member_var_classes(cls_cursor, 
                                                            keep_func)
        for member_cursor, member_cls_cursor in member_with_def_classes:
            dot_gen.add_composite_class(cls_cursor.spelling, 
                                        member_cursor.spelling,
                                        member_cls_cursor.spelling)
        callee_cursors = sem.get_class_callees(cls_cursor, keep_func)
        for callee in callee_cursors:
            callee_cls_cursor = sem.get_semantic_parent_of_decla_cursor(callee)
            dot_gen.add_callee_class(cls_cursor.spelling, 
                                     callee.spelling, 
                                     callee_cls_cursor.spelling)
            
    return dot_gen.get_dot_str()        
    