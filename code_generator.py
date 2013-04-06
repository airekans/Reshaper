'''
Created on 2013-2-19

@author: liangzhao
'''
from clang.cindex import Index, CursorKind, TypeKind


serialize_template = '''
template<class Archive>
void serialize(Archive & ar, const unsigned int version)
{
{%- for var in member_vars %}
       ar & {{ var }};
{%- endfor %}       
}
'''

eq_template = '''
friend bool operator == (const {{ class_name }} & a, const {{ class_name }}  & b)
{ 
          return ( 
{%- for var in member_vars %}    
                  a.{{ var }} == b.{{ var }} &&
{%- endfor %}
                  true);
 }
'''



def get_member_vars_from_children(children):
    member_vars = {}
    for child in children:
        if not child.kind == CursorKind.FIELD_DECL:
            continue
        if child.type.kind == TypeKind.POINTER:
            continue
        member_vars[child.spelling] = child.type.kind  
    return sorted(member_vars)



def match_class_name(cursor, class_name):
    return cursor.spelling == class_name and \
            (cursor.kind == CursorKind.CLASS_DECL or cursor.kind == CursorKind.STRUCT_DECL)

def get_member_vars_from_cursor(cursor, class_name):
    if(match_class_name(cursor, class_name)):
        return get_member_vars_from_children(cursor.get_children())
    else:
        for child in cursor.get_children():
            [member_vars_non_pt, member_vars_pt] = get_member_vars_from_cursor(child, class_name)
            if(member_vars_non_pt or member_vars_pt):
                return [member_vars_non_pt, member_vars_pt]
    return None


def get_member_variables(header_file, class_name):
    index = Index.create()
    tu = index.parse(header_file, args=['-x', 'c++'])
    if not tu:
        raise Exception('Cannot open header file %s' % header_file)
    return [get_member_vars_from_cursor(tu.cursor, class_name), [] ]


def generate_code(header_file, class_name):
    member_vars = get_member_variables(header_file, class_name)
    from jinja2 import Template
    
    code_templates = [eq_template, serialize_template]
    for code_template in code_templates:
        template = Template(code_template)
        print template.render(class_name=class_name, member_vars=member_vars)



