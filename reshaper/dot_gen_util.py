'''
Created on May 30, 2013

@author: liangzhao
'''

from jinja2 import Template
import semantic as sem, util

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
        
    def add_denpendency(self, label):
        if label in self._label2node:
            return
        
        node = 'Node%d' % (len(self._label2node)+1)                       
        
        self._label2node[label] = node
        
        template = Template(NODE_TEMPLATE)
                
        self._dot_str += template.render(label=label, node = node)  
    
    def add_inherit_class(self, base_cls_name, child_cls_name):
        self.add_denpendency(base_cls_name)
        self.add_denpendency(child_cls_name)
        
        template = Template(INHERIT_TEMPLATE)
        base_node = self._label2node[base_cls_name]
        child_node = self._label2node[child_cls_name]
        
        self._dot_str += template.render(child=child_node, \
                                         base=base_node)
        
    def add_composite_class(self, cls_name, member_name, member_cls_name):
        self.add_denpendency(cls_name)
        self.add_denpendency(member_cls_name)
        
        template = Template(COMPOSITE_TEMPLATE)
        cls_node = self._label2node[cls_name]
        member_cls_node = self._label2node[member_cls_name]

        self._dot_str += template.render(cls=cls_node, \
                                         member_cls=member_cls_node,
                                         member=member_name)
    
    def add_callee_class(self, cls_name, callee_name, callee_cls_name):
        self.add_denpendency(cls_name)
        self.add_denpendency(callee_cls_name)
        
        template = Template(CALLEE_TEMPLATE)
        cls_node = self._label2node[cls_name]
        callee_cls_node = self._label2node[callee_cls_name]

        self._dot_str += template.render(caller_cls=cls_node, \
                                         callee_cls=callee_cls_node,
                                         callee=callee_name)
    
    def get_dot_str(self):
        
        head = \
'''
digraph G {
  rankdir = LR;
  edge [fontname="Helvetica",fontsize="10",labelfontname="Helvetica",labelfontsize="10"];
  node [fontname="Helvetica",fontsize="10",shape=record];''' 
        
        tail = '\n}'
        return head  + self._dot_str + tail


def walk_all_methods_def(_tu, class_name, func, on_no_callee):
    '''
    walk definition of all methods of class_name in _tu with func,
    signature of func is func(method_def_cursor, callee_decl_cursor),
    when a method has no callee, will pass it to on_no_callee 
    '''
    cls_cursor = sem.get_classes_with_names(_tu, class_name)[0]
    all_methods = sem.get_methods_from_class(cls_cursor)
    
    for method_cursor in all_methods:
        method_def = method_cursor.get_definition()
        if method_def is not None:
            cursors = util.get_cursors_if(method_def, \
                                         lambda c: c != method_def and \
                                         sem.is_member_of(c, cls_cursor.spelling))
            found_hash = set([]) 
            for cursor in cursors:
                decl_cusor = util.get_declaration(cursor)
                if decl_cusor == method_def or \
                    decl_cusor.hash in found_hash or \
                     not decl_cusor.spelling:
                    continue
                func(method_def, decl_cusor)
                found_hash.add(decl_cusor.hash)
                
            if not cursors:
                on_no_callee(method_def)


def gen_class_internal_relation_graph(_tu, class_name):
    dot_gen = DotGenertor()
    
    def walk_func(method_def_cursor, callee_decl_cursor):
        dot_gen.add_callee_class(method_def_cursor.spelling, '', 
                                 callee_decl_cursor.spelling)
    
    on_no_callee_cursor = lambda method_def_cursor: \
                            dot_gen.add_denpendency(method_def_cursor.spelling)
                        
    walk_all_methods_def(_tu, class_name, walk_func, on_no_callee_cursor)
                
    return dot_gen.get_dot_str()

def gen_class_collaboration_graph(_tu, class_names, source_dir= None, show_functions = True):
    '''
    generate class collaboration graph
    _tu: input tu
    class_names: input class names
    source_dir: if set, will only show the classes that define in this folder
    show_functions: if False, will not show function names
    '''
    dot_gen = DotGenertor()
    cls_cursors = sem.get_classes_with_names(_tu, class_names)
    
    if source_dir:
        keep_func = lambda c : sem.is_cursor_in_dir(c, source_dir)
    else:
        keep_func = lambda c: True

    
    for cls_cursor in cls_cursors:
        ref_cls_names = set([])  
        
        base_cursors = sem.get_base_cls_cursors(cls_cursor)
        for base in base_cursors:
            dot_gen.add_inherit_class(base.spelling, cls_cursor.spelling)
              
        member_with_def_classes = sem.get_member_var_classes(cls_cursor, 
                                                            keep_func)
        for member_cursor, member_cls_cursor in member_with_def_classes:
            member_cls_name = member_cls_cursor.spelling
            ref_cls_names.add(member_cls_name)
            dot_gen.add_composite_class(cls_cursor.spelling, 
                                        member_cursor.spelling,
                                        member_cls_name)
            
        callee_cursors = sem.get_class_callees(cls_cursor, keep_func)
        for callee in callee_cursors:
            callee_cls_cursor = sem.get_semantic_parent_of_decla_cursor(callee)
            callee_cls_name = callee_cls_cursor.spelling
            if show_functions:
                dot_gen.add_callee_class(cls_cursor.spelling, 
                                         callee.spelling, 
                                         callee_cls_name)
            elif callee_cls_name not in ref_cls_names:
                dot_gen.add_callee_class(cls_cursor.spelling, 
                                         '<use>', 
                                         callee_cls_name)
                ref_cls_names.add(callee_cls_name)
            
    return dot_gen.get_dot_str()        
    
