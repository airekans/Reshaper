'''
Created on 2013-2-19

@author: liangzhao
'''

SERIALIZE_TEMPLATE = '''\
///serialization function for class {{ class_name }}:
template<class Archive>
void serialize(Archive & ar, const unsigned int version)
{
{%- for var in member_vars %}
    ar & BOOST_SERIALIZATION_NVP({{ var }});
{%- endfor %}       
}\
'''

EQ_TEMPLATE = '''\
friend bool operator == (const {{ class_name }}& a, const {{ class_name }}& b)
{ 
          return ( 
{%- for var in nonpt_member_vars %}    
                  a.{{ var }} == b.{{ var }} &&
{%- endfor %}
{%- for var in pt_member_vars %}    
                  *(a.{{ var }}) == *(b.{{ var }}) &&
{%- endfor %}
                  true);
}\
'''

import reshaper.semantic as sem
from jinja2 import Template
from reshaper import util
import logging


class ClassSerializer(object):
    def __init__(self, class_cursor):
        assert(class_cursor is not None)
        assert(class_cursor.is_definition())
        
        self.cursor = class_cursor
        self._class_name = class_cursor.spelling
    
    def render(self, code_template, **kwargs):
        all_val_empty = True
        for var in kwargs.values():
            if var:
                all_val_empty = False
                break
        if all_val_empty:
            logging.info('no member found for %s' % self._class_name)
            return "" 
        
        kwargs['class_name'] = self._class_name
        template = Template(code_template)
        return template.render(kwargs)
    

def gen_code_with_member_var_separated(code_template,
                                       class_cursor = None):
    '''
    generate code for a class with member variables, 
    separate pointer and non pointer types 
    '''
    cs = ClassSerializer(class_cursor) 
      
    nonpt_member_vars = sem.get_non_static_nonpt_var_names(cs.cursor)
    pt_member_vars = sem.get_non_static_pt_var_names(cs.cursor)
        
    return cs.render(code_template,
                     nonpt_member_vars = nonpt_member_vars,
                     pt_member_vars = pt_member_vars)
    
def gen_code_with_member_var(code_template,
                             class_cursor = None):
    '''
    generate code for a class with member variables
    '''
   
    cs = ClassSerializer(class_cursor) 
      
    member_vars = sem.get_non_static_var_names(cs.cursor)
    return cs.render(code_template, member_vars = member_vars)    
    

def generate_serialize_code(class_cursor):
    ''' generate serialization code for a c++ class '''
    return gen_code_with_member_var(SERIALIZE_TEMPLATE,
                                    class_cursor)

def generate_eq_op_code(class_cursor):
    ''' generate operator== code for a c++ class '''
    return gen_code_with_member_var_separated(EQ_TEMPLATE,
                                              class_cursor)

