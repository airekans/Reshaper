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

import reshaper.header_util as hu
from jinja2 import Template
from reshaper import util
import logging


class ClassSerializer(object):
    def __init__(self, header_path, class_name):
        _tu = util.get_tu(header_path)
        self.cursor = hu.get_class_cursor(_tu.cursor, class_name, header_path)
        
        if not self.cursor:
            raise Exception("Can not find class definition for %s in %s" % \
                            (class_name, header_path))
        self._class_name = class_name
    
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
    

def gen_code_with_member_var_separated(header_path, 
                                        class_name, 
                                        code_template):
    '''
    generate code for a class with member variables, 
    separate pointer and non pointer types 
    '''
    cs = ClassSerializer(header_path, class_name) 
      
    nonpt_member_vars = hu.get_non_static_nonpt_var_names(cs.cursor)
    pt_member_vars = hu.get_non_static_pt_var_names(cs.cursor)
        
    return cs.render(code_template,
                     nonpt_member_vars = nonpt_member_vars,
                     pt_member_vars = pt_member_vars)
    
def gen_code_with_member_var(header_path,
                             class_name, 
                             code_template):
    '''
    generate code for a class with member variables
    '''
   
    cs = ClassSerializer(header_path, class_name) 
      
    member_vars = hu.get_non_static_var_names(cs.cursor)
        
    return cs.render(code_template, member_vars = member_vars)    
    
   
    
    

def generate_serialize_code(header_path, class_name):
    ''' generate serialization code for a c++ class '''
    return gen_code_with_member_var(header_path,
                                    class_name,
                                    SERIALIZE_TEMPLATE)

def generate_eq_op_code(header_path, class_name):
    ''' generate operator== code for a c++ class '''
    return gen_code_with_member_var_separated(header_path,
                                            class_name,
                                            EQ_TEMPLATE)

