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
import sys


def gen_code_with_member_var_separated(header_path, 
                                        class_name, 
                                        code_template):
    '''
    generate code for a class with member variables, 
    separate pointer and non pointer types 
    '''
    tu_ = util.get_tu(header_path)
    cursor = hu.get_class_cursor(tu_.cursor, class_name, header_path)
    
    if not cursor:
        print "Can not find class definition for %s in %s" \
                % (class_name, header_path)
        sys.exit(1)
      
    nonpt_member_vars = hu.get_non_static_nonpt_var_names(cursor)
    pt_member_vars = hu.get_non_static_pt_var_names(cursor)
    
    if not nonpt_member_vars and not pt_member_vars:
        print 'no member found for %s' % class_name
        return
    
    from jinja2 import Template
       
    template = Template(code_template)
    return template.render(class_name=class_name,
                           nonpt_member_vars = nonpt_member_vars,
                           pt_member_vars = pt_member_vars)
    
def gen_code_with_member_var(header_path,
                             class_name, 
                             code_template):
    '''
    generate code for a class with member variables
    '''
    _tu = util.get_tu(header_path)
    cursor = hu.get_class_cursor(_tu.cursor, class_name, header_path)
    
    if not cursor:
        raise Exception("Can not find class definition for %s in %s" % \
                        (class_name, header_path))
        
    
    member_vars = hu.get_non_static_var_names(cursor)
    if not member_vars:
        print 'no member found for %s' % class_name
        return ""
       
       
    template = Template(code_template)
    return template.render(class_name=class_name,
                           member_vars = member_vars)
    
    

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

