''' This module contains functions process the AST from cursor.
'''

from clang.cindex import Cursor
import pickle
from clang.cindex import Config

_CONF = Config()

class TypeKindCache(object):
    '''cache of TypeKind
    '''
    def __init__(self, type_kind):
        self.name = type_kind.name
        self.spelling = type_kind.spelling
    def __eq__(self, type_kind):
        return self.name == type_kind.name
    def __cmp__(self, type_kind):
        return cmp(self.name, type_kind.name)

class TypeCache(object):
    '''cache of Type'''
    def __init__(self, t):
        self.kind = TypeKindCache(t.kind)

class CursorKindCache(object):
    '''cache of CursorKind '''
    def __init__(self, kind):
        self.name = kind.name
        
    def __eq__(self, kind):
        return self.name == kind.name 
    
    def __cmp__(self, kind):
        return cmp(self.name, kind.name)

class FileCache(object):
    ''' cache of File'''
    def __init__(self, file_):
        self.name = file_.name

class LocationCache(object):
    ''' cache of Location'''
    def __init__(self, location):
        self.column = location.column
        self.line = location.line
        if location.file:
            self.file = FileCache(location.file)
        else:
            self.file = None

class ExtentCache(object):
    '''cache of Extent'''
    def __init__(self, extent):
        self.start = LocationCache(extent.start)
        self.end = LocationCache(extent.end)

class TokenCache(object):
    def __init__(self, token):
        self.extent = ExtentCache(token.extent)
        self.spelling =  token.spelling




class CursorCache(object):
    ''' Cache for Cursor'''
    cursor2cache = {}

    def __init__(self, cursor, keep_func = lambda c: True):
        
        self._cursor = cursor
        self._keep_func = keep_func
        
        self.spelling = cursor.spelling 
        self.displayname = cursor.displayname
        self.kind = CursorKindCache(cursor.kind)
        self._is_definition = cursor.is_definition()
        self.location = LocationCache(cursor.location)
        self.type = TypeCache(cursor.type)
        
        self._usr = cursor.get_usr()
        self._definition = None
        self._declaration = None
        self.semantic_parent =  None
        self._parent =  None
        
        self._tokens = []
        for t in cursor.get_tokens():
            self._tokens.append(TokenCache(t))

        self._children = []
        
        for c in cursor.get_children():
            if not keep_func(c):
                continue
            child = CursorCache(c, keep_func)
            child.set_parent(self)
            self._children.append(child)
       
        key = cursor.hash
        CursorCache.cursor2cache[key] = self
   
   
   
    def create_ref_cursor_cache(self, ref_cursor):
        return CursorCache.do_create_ref_cursor_cache(ref_cursor, \
                                                      self._keep_func)
    
            
    @staticmethod
    def do_create_ref_cursor_cache(ref_cursor, keep_func):
        
        if not ref_cursor:
            return None
        
        key = ref_cursor.hash
        if key in CursorCache.cursor2cache:
            return CursorCache.cursor2cache[key]
        else:
            return CursorCache(ref_cursor, keep_func)
    
    def update_ref_cursors(self):
        _definition = self._cursor.get_definition()
        self._definition = self.create_ref_cursor_cache(_definition)
         
        _declaration = _CONF.lib.clang_getCursorReferenced(self._cursor)
        self._declaration = self.create_ref_cursor_cache(_declaration)
        
        _semantic_parent = self._cursor.semantic_parent 
        self.semantic_parent = self.create_ref_cursor_cache(_semantic_parent)
        
        for c in self._children:
            c.update_ref_cursors()
        
    
    def __getstate__(self):
        dic_copy = dict(self.__dict__)
        del dic_copy['_keep_func']
        del dic_copy['_cursor'] 
        return dic_copy    
        
    def get_children(self):    
        return self._children
   
    def get_tokens(self): 
        return self._tokens
    
    def print_all(self, level =0):
        prefix = "**" * level
        print prefix + "spelling:", self.spelling
        print prefix + "displayname:", self.displayname
        print prefix + "kind:", self.kind
        for c in self._children:
            c.print_all(level+1)
    
    def is_definition(self):
        return self._is_definition
 
    def get_definition(self):
        return self._definition
    
    def get_declaration(self):
        return self._declaration
    
    def get_usr(self):
        return self._usr
    
    def get_parent(self):
        return self._parent
    
    def set_parent(self, parent):
        self._parent =  parent

class DiagnosticCache(object):
    def __init__(self, diag):
        self.spelling =  diag.spelling


class TUCache(object):
    def __init__(self, tu):
        CursorCache.cursor2cache.clear()
        self.cursor = CursorCache(tu.cursor)
        self.cursor.update_ref_cursors()
        self.diagnostics = []
        for diag in tu.diagnostics:
            self.diagnostics.append(DiagnosticCache(diag))
        
    def dump(self,file_path):
        pickle.dump(self, open(file_path,'w'))
    
    @staticmethod 
    def load(file_path):    
        return pickle.load(open(file_path))
        
    def get_parent(self):
        return None   
       



        