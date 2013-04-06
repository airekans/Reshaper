'''
Created on 2013-2-19

@author: liangzhao
'''
from clang.cindex import Index, CursorKind, TypeKind


serialize_template = '''\
template<class Archive>
void serialize(Archive & ar, const unsigned int version)
{
{%- for var in nonpt_member_vars %}
    ar & {{ var }};
{%- endfor %}       
{%- if pt_member_vars %}
    //todo: the following pointer type members are not serialized 
{%- endif %}
{%- for var in pt_member_vars %}
    // {{ var }};
{%- endfor %} 
}\
'''

eq_template = '''\
friend bool operator == (const {{ class_name }} & a, const {{ class_name }}  & b)
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


import header_util as hu

def do_generate_code(header_path, class_name, code_template):
    tu = hu.parse(header_path)
    cursor = hu.get_class_decl_cursor(tu.cursor, class_name)
    nonpt_member_vars = hu.non_static_nonpt_var_names(cursor)
    pt_member_vars = hu.non_static_pt_var_names(cursor)
    from jinja2 import Template
       
    template = Template(code_template)
    return template.render(class_name=class_name,
                           nonpt_member_vars = nonpt_member_vars,
                           pt_member_vars = pt_member_vars)

def generate_serialize_code(header_path, class_name):
    return do_generate_code(header_path, class_name, serialize_template)

def generate_eq_op_code(header_path, class_name):
    return do_generate_code(header_path, class_name, eq_template)

