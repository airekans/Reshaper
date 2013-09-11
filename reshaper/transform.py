'''
Created on Aug 30, 2013

@author: jcchentmp
'''
import reshaper.semantic as sem
from clang.cindex import CursorKind, CXXAccessSpecifier
from reshaper.util import get_cursors_if    
from reshaper.find_reference_util import get_usr_of_declaration_cursor
from reshaper.find_reference_util import get_cursors_with_name
from reshaper.find_reference_util import filter_cursors_by_usr
from functools import partial
from reshaper.ast import get_tu
from reshaper.util import get_cursor_if


def is_public_access_decl(cursor):
    '''access if an access specifier decleration is public
    '''
    if cursor.get_access_specifier() == CXXAccessSpecifier.PUBLIC:
        return True
    else:
        return False
    
def find_public_fields(cls_cursor):
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
    for child in children:
        if child.kind == CursorKind.CXX_ACCESS_SPEC_DECL:
            is_public = is_public_access_decl(child)
        elif child.kind == CursorKind.FIELD_DECL and is_public:
            public_fields.append(child)
        else:
            continue
        
    return public_fields

def get_private_assecc_cursor(cls_cursor):
    '''get 'private:' cursor inside a class
    '''
    children = cls_cursor.get_children()
    for child in children:
        if child.kind == CursorKind.CXX_ACCESS_SPEC_DECL and not is_public_access_decl(child):
            return child

def find_reference_to_field(fld_cursor, directory):
    '''find reference to a field
    '''
    reference_usr = get_usr_of_declaration_cursor(fld_cursor)
    
    refer_curs = []
    sem.scan_dir_parse_files(directory, \
            partial(get_cursors_with_name, \
                    name = fld_cursor.spelling, \
                    ref_curs = refer_curs))
    refer_curs = filter_cursors_by_usr(refer_curs, reference_usr)
    
    return refer_curs


def get_binary_operator(cursor):
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

def use_set_method(ref_cursor, tu):
    '''decide if a cursor uses set method
    '''
    bi_opt_cursors = get_cursors_if(tu, lambda cur: cur.kind == CursorKind.BINARY_OPERATOR \
                              and cur.extent.start.offset <= ref_cursor.extent.start.offset \
                              and cur.extent.end.offset >= ref_cursor.extent.end.offset)
    
    for cur in bi_opt_cursors:
        if  get_binary_operator(cur) == '='\
            and cur.get_children().next().extent.start.offset == ref_cursor.extent.start.offset \
            and cur.get_children().next().extent.end.offset == ref_cursor.extent.end.offset:
            ref_cursor.the_parent = cur
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
    
def add_fields(cursors, tu):
    '''add necessary attributes to cursor
    '''
    for cursor in cursors:
        if cursor.kind == CursorKind.MEMBER_REF_EXPR:
            cursor.use_set_method = use_set_method(cursor, tu)
        else:
            cursor.use_set_method = None
            
        if cursor.use_set_method:
            cursor.start_offset = cursor.the_parent.extent.start.offset
            cursor.end_offset = cursor.the_parent.extent.end.offset
        else:
            cursor.start_offset = cursor.extent.start.offset
            cursor.end_offset = cursor.extent.end.offset
            
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
        
    
    
def transform(input_file, class_names, directory):
    '''major function to transform public variables
    '''
    tu = get_tu(input_file)
    
    ref_cursors = []
    public_fields = []
    
    for class_name in class_names:    
        class_cursor = get_cursor_if(tu, lambda cur: sem.is_class(cur) \
            and sem.is_class_name_matched(cur, class_name))
        class_public_fields = find_public_fields(class_cursor)
        pvt_acc_cursor = get_private_assecc_cursor(class_cursor)
        pvt_acc_cursor.fields = class_public_fields
        ref_cursors += [pvt_acc_cursor]
        public_fields += class_public_fields
    
    for field in public_fields:
        ref_cursors = ref_cursors + find_reference_to_field(field, directory)
        
    add_fields(ref_cursors, tu)
                
    cursors_in_files = organize_cursors_by_file(ref_cursors)
    
    for afile in cursors_in_files:
        with open(afile + '.bak', 'w') as fp:
            fp.write(generate_output_str(afile, cursors_in_files[afile]))
#        print generate_output_str(afile, cursors_in_files[afile])
    
def set_modification_offset(offset, cursor, cursor_list):
    '''change cursor's extent when it's extent is influenced by change of other cursor
    '''
    for cur in cursor_list:
        if cur.start_offset >= cursor.start_offset and cur.end_offset <= cursor.end_offset \
            and cur != cursor:
            cur.start_offset += offset
            cur.end_offset += offset

def get_func_name_suffix(name):
    '''get variable suffix
    '''
    if name.startswith('m_'):
        return name[2:].capitalize()
    else:
        return name.capitalize()


def generate_output_str(input_file, cursor_list):
    '''generate output for each file based on its cursors
    '''
    with open(input_file, 'r') as fp:
        file_str = fp.read()
        
    cursor_list = sorted(cursor_list, key = lambda cur: (cur.end_offset, \
        cur.end_offset - cur.start_offset), reverse = True)
    
    for cursor in cursor_list:
        name_suffix = get_func_name_suffix(cursor.displayname)
        
        if cursor.kind == CursorKind.MEMBER_REF_EXPR:
            if cursor.use_set_method:
                left_extent = (cursor.extent.start.offset, cursor.extent.end.offset)
                children = cursor.the_parent.get_children()
                children.next()
                right_cursor = children.next()
                right_extent = (right_cursor.extent.start.offset, right_cursor.extent.end.offset)
                
                sub_str = file_str[left_extent[0] : left_extent[1]].replace(cursor.displayname, \
                        'Set' + name_suffix + '(')
                offset = len(sub_str) - (right_extent[0] - left_extent[0])
                
                sub_str += file_str[right_extent[0] : right_extent[1]] + ')'
                file_str = file_str[: cursor.start_offset] + sub_str + file_str[cursor.end_offset :]
                
                set_modification_offset(offset, cursor, cursor_list)
                
            else:
                sub_str = file_str[cursor.start_offset : cursor.end_offset]
                sub_str = sub_str.replace(cursor.displayname, 'Get' + name_suffix + '()')
                file_str = file_str[: cursor.start_offset] + sub_str + file_str[cursor.end_offset :]
        
        elif cursor.kind == CursorKind.FIELD_DECL:
            space = ""
            index = cursor.start_offset - 1
            while file_str[index] != '\n':
                space += file_str[index]
                index -= 1
            
            sub_str = cursor.type.kind.name.lower() + ' Get' + name_suffix + '()\n'
            sub_str += space + '{\n\t' + space +  'return this.' + cursor.displayname + ';\n' + space + '}'
            if cursor.has_set_method:
                sub_str += ';\n' + space + 'void Set' + name_suffix \
                    + '(' + cursor.type.kind.name.lower() + ' val)\n'
                sub_str += space + '{\n\t' + space + 'this.' + cursor.displayname + '= val;\n' + space + '}' 
            file_str = file_str[: cursor.start_offset] + sub_str + file_str[cursor.end_offset :]
            
        elif cursor.kind == CursorKind.CXX_ACCESS_SPEC_DECL:
            space = "\t"            
            sub_str = "\n"
            for field_cur in cursor.fields:
                sub_str += space + field_cur.type.kind.name.lower() + ' ' + field_cur.displayname + ';\n'
            file_str = file_str[:cursor.end_offset] + sub_str + file_str[cursor.end_offset :]
                
    return file_str
        
    
        
        
    
    
    
    
    
