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
    def __eq__(self, kind):
        return self.name == kind.name

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

class LocationCache(object):
    def __init__(self, location):
        self.column = location.column
        self.line = location.line

class ExtentCache(object):
    '''cache of Extent'''
    def __init__(self, extent):
        self.start = LocationCache(extent.start)
        self.end = LocationCache(extent.end)

class TokenCache(object):
    def __init__(self, token):
        self.extent = ExtentCache(token.extent)
        self.spelling =  token.spelling


def memorized(class_):
    instances = {}
    def getinstance(*args, **kwargs):
        c_id = id(args[0])
        if c_id not in instances:
            instances[c_id] = class_(*args, **kwargs)
            return instances[c_id]
        return getinstance

@memorized
class CursorCache(object):
    cursor2cache = {}
    
#     def __new__(cls,  cursor, keep_func = lambda c: True):
#         if cursor is None:
#             return None
#         
#         cursor_id = id(cursor)
#         if CursorCache.cursor2cache.get(cursor_id):
#             return CursorCache.cursor2cache[cursor_id]
#         else:
#             return super(CursorCache, cls).__new__(cls, cursor, keep_func)   
    
    def __init__(self, cursor, keep_func = lambda c: True):
        
#         cursor_id = id(cursor)
#         if CursorCache.cursor2cache.get(cursor_id):
#             return
        
        
        self.spelling = cursor.spelling 
        self.displayname = cursor.displayname
        self.kind = CursorKindCache(cursor.kind)
        self._is_definition = cursor.is_definition()
        self.location = LocationCache(cursor.location)
        self.type = TypeCache(cursor.type)
        
#         _definition = cursor.get_definition()
#         
#         if(_definition and _definition != cursor):
#             self._definition = CursorCache(_definition, keep_func)
#         else:
#             self._definition = self
#         
#         _declaration = _CONF.lib.clang_getCursorReferenced(cursor)
#         if(_declaration and _declaration != cursor):
#             self._declaration = CursorCache(_declaration, keep_func)
#         else:
#             self._declaration = self
        
        self._tokens = []
        for t in cursor.get_tokens():
            self._tokens.append(TokenCache(t))
        
        self._children = []
        
        for c in cursor.get_children():
            if not keep_func(c):
                continue
            self._children.append(CursorCache(c, keep_func))
            
        #CursorCache.cursor2cache[cursor_id] = self 
        
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
    
#     def is_definition(self):
#         return self._is_definition
# 
#     def get_definition(self):
#         return self._definition
    
#     def get_declaration(self):
#         return self._declaration

class DiagnosticCache(object):
    def __init__(self, diag):
        self.spelling =  diag.spelling


class TUCache(object):
    def __init__(self, tu):
        self.cursor = CursorCache(tu.cursor)
        print len(CursorCache.cursor2cache)
        self.diagnostics = []
        for diag in tu.diagnostics:
            self.diagnostics.append(DiagnosticCache(diag))
        
    def dump(self,file_path):
        pickle.dump(self, open(file_path,'w'))
    
    @staticmethod 
    def load(file_path):    
        return pickle.load(open(file_path))
        
        
class StaticCursor(object):
    """ StaticCursor is a cursor that will not change the object ID
    after getting the children again and again.
    E.g. If you add an attribute to the child cursor, it will "disappear"
    after you get it again by using get_children.
    for child in cursor.get_children():
        child.parent = cursor
    for child in cursor.get_children():
        assert(hasattr(child, "parent")) # this will fail
    
    So you travese the AST easily with StaticCursor.

    Note that if you get cursor by using the native API of cindex,
    the return cursor will be Cursor instead of StaticCursor,
    so this operation will invalidate the static AST.
    
    """
    
    def __init__(self, cursor, parent = None):
        """ Create a new StaticCursor with a cindex.Cursor
        and a optional parent
        """

        self.__cursor = cursor
        self.__parent = parent
        self.__children = [StaticCursor(child, self)
                           for child in cursor.get_children()]
        
    def get_parent(self):
        return self.__parent

    def get_children(self):
        """ Simulate the Cursor.get_children function
        """
        return self.__children

    def get_cursor(self):
        return self.__cursor

    def __getattr__(self, name):
        return getattr(self.__cursor, name)
        

def get_static_ast(source):
    """Get static AST from the given cursor or translation unit.
    AST from cursor is dynamic, i.e. they will change if the code is changed after
    you got the cursor.

    We need a static AST and extra information to make AST processing easier.
    parent and children will be add to the cursor.
    
    Arguments:
    - `source`: Cursor or TranslationUnit the AST rooted at.
    """

    if source is None:
        return None
    elif isinstance(source, Cursor):
        cursor = source
    else: 
        # Assume TU
        cursor = source.cursor

    return StaticCursor(cursor)

        