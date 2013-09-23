"""util functions for finding reference
"""
import os, sys
from clang.cindex import CursorKind, TypeKind
from reshaper.util import  check_diagnostics
from reshaper.ast import get_tu
from reshaper.util import walk_ast, get_cursors_if, get_declaration
from reshaper.semantic import get_cursors_add_parent, is_cursor
from reshaper.option import setup_find_reference_options
from optparse import OptionParser
from functools import partial

_class_mem_cursorkind = \
        ("CONSTRUCTOR", "DESTRUCTOR", "CXX_METHOD", "FIELD_DECL")

class ClassInfo(object):
    """get class info include member and functions
    from class cursor 
    """
    def __init__(self, cursor):
        """ should make sure that cursor.kind is one of 
        CLASS_DECL or STRUCT_DECL
        """
        if cursor is None or cursor.kind is None:
            return

        if not cursor.kind == CursorKind.CLASS_DECL:
            return

        self._cursor = cursor
        self._class_name = cursor.displayname
        self._mem_fun_dict = {}
        self._mem_dict = {}
        self._update_mem_dicts()

    def _update_mem_dicts(self):
        """internal function, used to parse class cursor 
        and get infors
        """
        def walk_ast_cursor_fun(cursor, level, mem_dict, mem_fun_dict):
            """function used in walk_ast
            """
            if cursor.kind and cursor.kind.name in _class_mem_cursorkind:
                if cursor.kind == CursorKind.FIELD_DECL:

                    def get_mem_tokens(cursor):
                        """get string of tokens from cursor for mem
                        """
                        if not cursor or not cursor.kind or \
                                not cursor.kind == CursorKind.FIELD_DECL:
                            return None

                        tokens_str = ""
                        for token in cursor.get_tokens():
                            if token.spelling == cursor.displayname:
                                tokens_str += " " + token.spelling
                            else:
                                tokens_str += token.spelling
                        return tokens_str

                    mem_dict[cursor.get_usr()] = get_mem_tokens(cursor)
                else:
                    mem_fun_dict[cursor.get_usr()] = cursor.displayname
        walk_ast(self._cursor, partial(walk_ast_cursor_fun, \
                mem_dict = self._mem_dict, mem_fun_dict = self._mem_fun_dict))


    def get_class_name(self):
        """return paser class name
        """
        return self._class_name

    def get_mem_list(self):
        """return mem list of class
        """
        return self._mem_dict.values()

    def get_mem_usr_list(self):
        """return usr list of mems in class
        """
        return self._mem_dict.keys()

    def get_mem_func_list(self):
        """return func list of class
        """
        return self._mem_fun_dict.values()

    def get_mem_func_usr_list(self):
        """return usrs of funcs in class
        """
        return self._mem_fun_dict.keys()

    def get_mem_with_usr_dict(self):
        """return dict of 
        {mem_usr, mem_tokens}
        """
        return self._mem_dict

    def get_mem_func_with_ust_dict(self):
        """return dict of 
        {func_usr, func_displayname}
        """
        return self._mem_fun_dict


class FileClassInfo(object):
    """parse file or tu to get ClassInfo object
    for all classes and structs
    """
    def __init__(self, filename, cdb_path = None, source_tu = None):
        """1) should make sure that filename exists 
           2) you can also pass tu object to it
        """
        if source_tu is not None:
            self._file_tu = source_tu
        else:
            self._file_tu = get_tu(os.path.abspath(filename), \
                    cdb_path = cdb_path)
            if self._file_tu is None:
                return

        class_cursors = self._get_class_cursors()
        self._class_to_info_dict = {}
        for cursor in class_cursors:
            self._class_to_info_dict[cursor.displayname]  = \
                    ClassInfo(cursor)

    def _get_class_cursors(self):
        """get class and struct cursors in tu
        """
        def is_class_cursor(cursor):
            if cursor and cursor.kind:
                if cursor.kind == CursorKind.CLASS_DECL\
                        or cursor.kind == CursorKind.STRUCT_DECL:
                    return True
            return False

        class_cursors = get_cursors_if(self._file_tu, is_class_cursor)
        return class_cursors

    def get_class_with_inf_dict(self):
        """return classes info format with
        {class_name, ClassInfo}
        """
        return self._class_to_info_dict

    def get_class_list(self):
        """return class name list
        """
        return self._class_to_info_dict.keys()

    def get_class_info_list(self):
        """return class_info list
        """
        return self._class_to_info_dict.values()

    def get_class_info_with_name(self, name):
        """get class info with name
        """
        return self._class_to_info_dict[name]
        
class CallInfo(object):
    """serialize and deserialize for 
    caller and caller str.
       Format is as follows:
       caller:value1,value2,...,:callee:value1,...
    value can be any kind of str.(location and usr)

    caller_callee_split is the split between caller and
    callee, inter_split is the split between callers
    and callees, key_value_split is the split between 
    caller(callee) and value
    """
    def __init__(self, input_str,\
            caller_callee_split = ";", inter_split = ",",\
            key_value_split = "|"):
        """if input_str is not None, should make sure
        it in the format of "caller..;caller"
        """
        self._caller_callee_split = caller_callee_split
        self._inter_split = inter_split
        self._key_value_split = key_value_split

        if input_str is None or input_str == "":
            self._callers_str = ""
            self._callees_str = ""
            return 

        split_str = input_str.split(caller_callee_split)
        assert(len(split_str) == 2)

        self._callers_str = \
                split_str[0].split(key_value_split)[1]
        self._callees_str = \
                split_str[1].split(key_value_split)[1]

    def get_caller(self):
        """return callers_str in the format of
        value1,value2
        """
        return self._callers_str

    def get_caller_list(self):
        """return callers in the format of 
        [value1, value2]
        """
        return self._callers_str.split(self._inter_split)

    def get_callee(self):
        """return callees_str in the format of 
        value1,value2
        """
        return self._callees_str

    def get_callee_list(self):
        """return callee str in the format of
        [value1, value]
        """
        return self._callees_str.split(self._inter_split)

    def add_caller(self, caller_str):
        """add caller_str
        """
        should_add = False
        if caller_str is not None:
            if self._callers_str == "":
                should_add = True
            elif not caller_str in self._callers_str:
                should_add = True

        if should_add:
            if self._callers_str == "":
                self._callers_str = "%s" % caller_str
            else:
                self._callers_str = "%s%s%s" % \
                        (self._callers_str, self._inter_split, caller_str)

    def add_callee(self, callee_str):
        """add callee str
        """
        should_add = False
        if callee_str is not None:
            if self._callees_str == "":
                should_add = True
            elif not callee_str in self._callees_str:
                should_add = True

        if should_add:
            if self._callees_str == "":
                self._callees_str = callee_str
            else:
                self._callees_str = "%s%s%s" \
                    % (self._callees_str, self._inter_split, callee_str)

    def clear(self):
        """clear callees_str and callers_str
        """
        self._callees_str = ""
        self._callers_str = ""

    def get_callers_callees_str(self):
        """return callers and callees str
        """
        return "caller%s%s%scallee%s%s" % \
                (self._key_value_split, self._callers_str, \
                self._caller_callee_split, self._key_value_split, \
                self._callees_str)

def get_usr_of_declaration_cursor(cursor):
    """get declaration cursor and return its USR
    """
    declaration_cursor = get_declaration(cursor)
    if is_cursor(declaration_cursor):
        return declaration_cursor.get_usr()
    return None

def filter_cursors_by_usr(cursors, target_usr):
    """the input cursors are gotten from tu only by its spelling and 
    displayname, so there may be many fake ones that with the same
    displayname but not the referece we want.
    Then, we need to remove the fake cursors by usr and return the 
    cursors we want.
    """
    cursor_dict = {}
    for cursor in cursors:
        if cursor.kind == CursorKind.CALL_EXPR and \
           len(list(cursor.get_children())) > 0:
            continue
        
        cursor_usr = get_usr_of_declaration_cursor(cursor)
        
        #FIXME:template class and template function;
        #its declaration USR is different from USR 
        if cursor_usr == target_usr:
            location = cursor.location
            key = (os.path.abspath(location.file.name), \
                    location.line, location.column)
            cursor_dict[key] = cursor

    return [cursor_dict[key] for key in sorted(cursor_dict.keys())]

def get_cursors_with_name(file_name, name, ref_curs):
    """call back pass to semantic.scan_dir_parse_files 
       to parse files
    """
    if not os.path.exists(file_name):
        sys.stderr.write("file %s don't exists\n" % file_name)
        return
    current_tu = get_tu(file_name)
    if check_diagnostics(current_tu.diagnostics):
        sys.stderr.write("Warning : diagnostics occurs, skip file %s\n" % file_name)
        # return

    cursors = get_cursors_add_parent(current_tu, name)
    #don't forget to define global _refer_curs'
    ref_curs.extend(cursors)


def parse_find_reference_args(default_output_filename, args = None, prog = None):
    '''get user options and parse it for 
    finding reference
    arguments: args and prog are used for passing arguments during unit test 
    '''
    option_parser = OptionParser(usage = "%prog [options]", prog = prog)
    setup_find_reference_options(option_parser)
    options, args = option_parser.parse_args(args)

    #check input args
    if options.filename is None:
        option_parser.error("please input file to search")
    
    if not os.path.isfile(options.filename):
        option_parser.error("file %s is not exists, please check it!"\
                % options.filename)

    if options.spelling is None:
        option_parser.error("please input reference spelling")

    if options.line is None:
        option_parser.error("please input reference line No.")

    if options.column is None:
        print "Warning : forget to input column",
        print ", the first one in %s line %s will be used" \
                % (options.filename, options.line)

    if not options.output_file_name or \
        (os.path.isfile(options.output_file_name) and \
        not os.access(options.output_file_name, os.W_OK)):
        options.output_file_name = os.path.join('.', default_output_filename)

    return options

def walk_ast_add_caller(source, visitor, \
        is_visit_subtree_fun = lambda _c : True):
    """walk ast and add caller info (usr, location)
    to visitor func
    """
    if source is None:
        return
    elif hasattr(source, "get_children"):
        cursor = source
    else:
        cursor = source.cursor

    def walk_ast_and_add_caller(cursor, usr, location):
        """internal use
        """
        if not is_visit_subtree_fun(cursor):
            return

        visitor(cursor, usr, location)
        for c in cursor.get_children():
            caller_usr = usr
            location_str = location
            if caller_usr is None:
                caller_usr = get_usr_if_caller(c)
                if caller_usr is None:
                    location_str = None
                else:
                    location_str = get_declaration_location_str(c)

            walk_ast_and_add_caller(c, caller_usr, location_str)

    source_usr = get_usr_if_caller(cursor)
    if source_usr is None:
        source_location = None
    else:
        source_location = get_declaration_location_str(cursor)

    walk_ast_and_add_caller(cursor, source_usr, source_location)

def get_usr_if_caller(cursor):
    """if cursor is caller, return its usr
    """
    if cursor is None or cursor.type is None:
        return None

    if cursor.is_definition() and cursor.type.kind == TypeKind.FUNCTIONPROTO:
        return get_usr_of_declaration_cursor(cursor)

def get_declaration_location_str(cursor):
    """get cursor's declaration str info,
    return value's format is file.name-line-column
    """
    if cursor is None:
        return None
    decl_cursor = get_declaration(cursor)
    if decl_cursor is None or decl_cursor.location is None\
            or decl_cursor.location.file is None:
        return None

    location_str = "%s-%s-%s" % \
           (decl_cursor.location.file.name, decl_cursor.location.line,\
           decl_cursor.location.column)
    return location_str

def compare_file_name(cursor, level, base_filename):
    """compare if cursor is in base_filename or in its .h file;
    if cursor.location.file is not None, it will return True;
    this compare function is wrote for walk_ast as is_visit_subtree_fun
    """
    if cursor is None or cursor.location is None \
            or cursor.location.file is None:
        return True

    cursor_filename = cursor.location.file.name
    base_file_withoutext = os.path.splitext(os.path.basename(base_filename))[0]
    cursor_file_withoutext = os.path.splitext(os.path.basename(cursor_filename))[0]
    return base_file_withoutext == cursor_file_withoutext

