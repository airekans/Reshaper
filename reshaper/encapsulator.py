'''
Created on Aug 30, 2013

@author: Jingchuan Chen
'''
import reshaper.semantic as sem
from clang.cindex import CursorKind, CXXAccessSpecifier, TypeKind
from reshaper.find_reference_util import get_usr_of_declaration_cursor
from reshaper.find_reference_util import get_cursors_with_name
from reshaper.find_reference_util import filter_cursors_by_usr
from functools import partial
from reshaper.ast import get_tu
from reshaper.util import get_cursor_if
from jinja2 import Template
import logging
    
def find_public_fields(cls_cursor, fields = None):
    '''find public field inside a class
    '''
    if cls_cursor.kind == CursorKind.CLASS_DECL:
        is_public = False
    elif cls_cursor.kind == CursorKind.STRUCT_DECL:
        is_public = True
    else:
        return []
    
    public_fields = []
    children = cls_cursor.get_children()
    if fields:
        for child in children:
            if child.kind == CursorKind.CXX_ACCESS_SPEC_DECL:
                is_public = sem.is_public_access_decl(child)
            elif child.kind == CursorKind.FIELD_DECL\
                and is_public\
                and child.displayname in fields:
                
                fields.remove(child.displayname)
                public_fields.append(child)
            else:
                continue
        
        if fields:
            logging.warning("Cannot find public field %s in class %s" % \
                            (', '.join(fields), cls_cursor.displayname))
    else:
        for child in children:
            if child.kind == CursorKind.CXX_ACCESS_SPEC_DECL:
                is_public = sem.is_public_access_decl(child)
            elif child.kind == CursorKind.FIELD_DECL and is_public:
                public_fields.append(child)
            else:
                continue
        
    return public_fields

def get_prvt_fld_insert_location(cls_cursor):
    '''return first 'private:' specifier in class
        if the class has no 'private:' specifier
        the last cursor will be returned
    '''
    children = cls_cursor.get_children()
    for child in children:
        if child.kind == CursorKind.CXX_ACCESS_SPEC_DECL and not sem.is_public_access_decl(child):
            child.is_pvt_specfifier = True
            return child
    else:
        child.is_pvt_specfifier = False
        return child

def find_reference_to_field(fld_cursor, directory):
    '''find reference to a field
    '''
    reference_usr = get_usr_of_declaration_cursor(fld_cursor)
    
    refer_curs = []
    sem.walkdir(directory, \
            partial(get_cursors_with_name, \
                    name = fld_cursor.spelling, \
                    ref_curs = refer_curs))
    refer_curs = filter_cursors_by_usr(refer_curs, reference_usr)
    
    return refer_curs


def get_binary_operator_opt(cursor):
    '''get operator of a 'CursorKind.BINARY_OPERATOR' cursor
    '''
    if cursor.kind != CursorKind.BINARY_OPERATOR:
        return None
    else:
        tokens = cursor.get_tokens()
        for token in tokens:
            if token.cursor.extent == cursor.extent and token.cursor.kind == CursorKind.BINARY_OPERATOR:
                return token.spelling
    return None

def is_l_value(ref_cursor, tu):
    '''l value is the kind of value on the left hand side of '=' operator
        for example, in "i = 1;", "i" is l value
        left hand side value of '=' operator need to transformed to Set method
    '''
    if (ref_cursor.parent.kind == CursorKind.BINARY_OPERATOR 
        and get_binary_operator_opt(ref_cursor.parent) == '=' 
        and ref_cursor.parent.get_children().next() == ref_cursor): 
        #get_children().next() indicates left hand side of '=' operator
        return True
    elif (ref_cursor.parent.kind == CursorKind.CALL_EXPR
          and ref_cursor.parent.displayname == 'operator='
          and ref_cursor.parent.get_children().next() == ref_cursor):
        return True
    return False

def organize_cursors_by_file(ref_cursors):
    '''group cursors by file names and return a dictionary to represents file->cursors
    '''
    file_dict = {}
    for cursor in ref_cursors:
        fname = cursor.location.file.name
        if fname in file_dict:
            file_dict[fname] += [cursor]
        else:
            file_dict[fname] = [cursor]
    return file_dict

def get_func_name_suffix(name):
    '''get variable suffix
    '''
    if name.startswith('m_'):
        return name[2:].capitalize()
    else:
        return name.capitalize()

def filter_reference_in_cls_method(ref_cursors, cls_cursor):
    '''remove references inside class method
    '''
    methods = sem.get_methods_from_class(cls_cursor)
    extents = []
    for method in methods:
        def_cur = method.get_definition()
        if def_cur:
            extents += [(def_cur.extent.start.offset,
                           def_cur.extent.end.offset)]
    
    for cur in ref_cursors:
        for extent in extents:
            if cur.location.offset >= extent[0] \
                and cur.location.offset <= extent[1]:
                ref_cursors.remove(cur)
                break

def add_fields(cursors, tu):
    '''add necessary attributes to cursor
    '''
    for cursor in cursors:
        #setup use_set_methdo, it indicate which method to use when transforming
        if cursor.kind == CursorKind.MEMBER_REF_EXPR:
            cursor.use_set_method = is_l_value(cursor, tu)
        else:
            cursor.use_set_method = None
            
        #set method will influence a larger extent of file, offsets are used to
        #indicate the expanded extent 
        if cursor.use_set_method:
            cursor.start_offset = cursor.parent.extent.start.offset
            cursor.end_offset = cursor.parent.extent.end.offset
        else:
            cursor.start_offset = cursor.extent.start.offset
            cursor.end_offset = cursor.extent.end.offset
        
        #function name suffix
        cursor.suffix = get_func_name_suffix(cursor.displayname)
    
    #has_set_method is used to indicate whether a field need to have set method
    for cursor in cursors:
        if cursor.kind == CursorKind.FIELD_DECL:                    
            cursor_usr = get_usr_of_declaration_cursor(cursor)
            for cur in filter_cursors_by_usr(cursors, cursor_usr):
                if cur.use_set_method:
                    cursor.has_set_method = True
                    break
            else:
                cursor.has_set_method = False
        else:
            cursor.has_set_method = None

def filter_fields_has_get_set(fields, cls_cursor):
    '''remove the fields that already has getter or setter
    '''
    methods = sem.get_methods_from_class(cls_cursor)
    names = [cur.displayname[:-2] for cur in methods]
    
    for field in fields:
        suffix = get_func_name_suffix(field.displayname)
        if 'Get' + suffix in names \
            or 'Set' + suffix in names:
            logging.warning('Method %s in class %s already have Set/Get method, it will not be processed' \
                            % (field.displayname, cls_cursor.displayname))
            fields.remove(field)

def encapsulate(input_file, class_names, directory, fields):
    '''major function to encapsulate public variables
    '''
    tu = get_tu(input_file)
    
    ref_cursors = []
    
    for class_name in class_names:
        class_cursor = get_cursor_if(tu, lambda cur: sem.is_class(cur) \
            and sem.is_class_name_matched(cur, class_name))
        if not class_cursor:
            logging.error('Cannot find class %s in input file' % class_name)
        
        class_public_fields = find_public_fields(class_cursor, fields)
        
        if class_public_fields:
            pvt_acc_cursor = get_prvt_fld_insert_location(class_cursor)
            pvt_acc_cursor.fields = class_public_fields
            ref_cursors += [pvt_acc_cursor]
        
        filter_fields_has_get_set(class_public_fields, class_cursor)
        
        class_ref_cursors = []
        for field in class_public_fields:
            class_ref_cursors += find_reference_to_field(field, directory)
        filter_reference_in_cls_method(class_ref_cursors, class_cursor)
        
        ref_cursors += class_ref_cursors
        
        
        
    add_fields(ref_cursors, tu)
                
    cursors_in_files = organize_cursors_by_file(ref_cursors)
    
    for afile in cursors_in_files:
        file_str = generate_output_str(afile, cursors_in_files[afile])
#        print file_str
        with open(afile + '.bak', 'w') as fp:
            fp.write(file_str)
    
def change_offset_extent(offset, cursor, cursor_list):
    '''change cursor's extent when change on other cursor influence its offset
    '''
    for cur in cursor_list:
        if cur.start_offset >= cursor.start_offset and cur.end_offset <= cursor.end_offset \
            and cur != cursor:
            cur.start_offset += offset
            cur.end_offset += offset
        
def generate_output_str(input_file, cursor_list):
    '''generate output for each file based on its cursors
    '''
    transformer = FileTransformer(input_file)
        
    cursor_list = sorted(cursor_list, key = lambda cur: (cur.end_offset, \
        cur.end_offset - cur.start_offset), reverse = True)
    
    for cursor in cursor_list:
        if hasattr(cursor, 'is_pvt_specfifier'):
            transformer.trans_add_private(cursor)
        elif cursor.kind == CursorKind.MEMBER_REF_EXPR:
            if cursor.use_set_method:
                offset = transformer.trans_set(cursor)                
                change_offset_extent(offset, cursor, cursor_list)
            else:
                transformer.trans_get(cursor)
        
        elif cursor.kind == CursorKind.FIELD_DECL:
            transformer.trans_decl(cursor)
                
    return transformer.file_str
        
_GET_TEMPLATE = '''\
{{type}} Get{{suffix}}()
{{space}}{
{{space}}\treturn this.{{name}};
{{space}}}'''

_GET_TEMPLATE2 = '''\
const {{type}}& Get{{suffix}}() const
{{space}}{
{{space}}\treturn this.{{name}};
{{space}}};
{{space}}{{type}}& Get{{suffix}}()
{{space}}{
{{space}}\treturn this.{{name}};
{{space}}}'''

_SET_TEMPLATE = '''\
{{type}} Get{{suffix}}()
{{space}}{
{{space}}\treturn this.{{name}};
{{space}}};
{{space}}void Set{{suffix}}({{type}} val)
{{space}}{
{{space}}\tthis.{{name}} = val;
{{space}}}'''

_SET_TEMPLATE2 = '''\
const {{type}}& Get{{suffix}}() const
{{space}}{
{{space}}\treturn this.{{name}};
{{space}}};
{{space}}{{type}}& Get{{suffix}}()
{{space}}{
{{space}}\treturn this.{{name}};
{{space}}};
{{space}}void Set{{suffix}}({{type}} val)
{{space}}{
{{space}}\tthis.{{name}} = val;
{{space}}}'''

class FileTransformer:
    '''this class encapsulate a file to desirable output by calling methods with cursors
        each cursor identifies a kind of change
        cursors should be pass in descending order of cursor's end offset
    '''
    def __init__(self, input_file):
        '''init function
        '''
        with open(input_file, 'r') as fp:
            self.file_str = fp.read()
        
    def trans_set(self, cursor):
        '''encapsulate member field reference use Set
        '''
        for right_cursor in cursor.parent.get_children():
            #get last element of children list
            pass 
        right_extent = (right_cursor.extent.start.offset, right_cursor.extent.end.offset)
        left_extent = (cursor.extent.start.offset, cursor.extent.end.offset)
        
        sub_str = self.file_str[left_extent[0] : left_extent[1]].replace(cursor.displayname,
            'Set' + cursor.suffix + '(') + self.file_str[right_extent[0] : right_extent[1]] + ')'
        self.file_str = self.file_str[: cursor.start_offset] + sub_str + self.file_str[cursor.end_offset :]
        
        offset = len(sub_str) -1 - (right_extent[1] - left_extent[0])
        return offset
    
    def trans_get(self, cursor): 
        '''encapsulate member field reference use Get
        '''     
        sub_str = self.file_str[cursor.start_offset : cursor.end_offset]
        sub_str = sub_str.replace(cursor.displayname, 'Get' + cursor.suffix + '()')
        self.file_str = self.file_str[: cursor.start_offset] + sub_str + self.file_str[cursor.end_offset :]
        
    def trans_decl(self, cursor):
        '''encapsulate public field declaration to get and set methods 
        '''
        space = ""
        index = cursor.start_offset - 1
        while self.file_str[index] != '\n':
            space += self.file_str[index]
            index -= 1
        
        template = Template(self.get_template_str(cursor))
#        if cursor.has_set_method:
#            template = Template(_SET_TEMPLATE)
#        else:
#            template = Template(_GET_TEMPLATE)
        sub_str = template.render(space = space, type = cursor.type.spelling, 
                                  suffix = cursor.suffix, name = cursor.displayname)

        self.file_str = self.file_str[: cursor.start_offset] + sub_str + self.file_str[cursor.end_offset :]
    
    def trans_add_private(self, cursor):
        '''add transformed public field under private access specifier
        '''
        space = "\t"
        index = cursor.end_offset
        while self.file_str[index - 1] != '\n':
            index += 1
        
        if cursor.is_pvt_specfifier:
            sub_str = ''
        else:
            sub_str = 'private:\n'
        
        for field_cur in cursor.fields:
            sub_str += space + self.get_type_str(field_cur) + ' ' + field_cur.displayname + ';\n'
        self.file_str = self.file_str[:index] + sub_str + self.file_str[index:]

    def get_template_str(self, cursor):
        if cursor.has_set_method:
            if cursor.type.kind in [TypeKind.RECORD, TypeKind.UNEXPOSED]:
                return _SET_TEMPLATE2
            else:
                return _SET_TEMPLATE
        else:
            if cursor.type.kind in [TypeKind.RECORD, TypeKind.UNEXPOSED]:
                return _GET_TEMPLATE2
            else:
                return _GET_TEMPLATE
        
        
    def get_type_str(self, cursor, for_get_obj = False):
        if cursor.type.kind == TypeKind.RECORD and for_get_obj:
            #class and struct
            return 'const ' + cursor.type.spelling + '&'
        
        elif cursor.type.kind == TypeKind.UNEXPOSED and for_get_obj:
            #class template
            return 'const ' + cursor.type.spelling + '&'
        
        return cursor.type.spelling
    
        
        
        
        
        
        
        
        
