''' This module contains functions process the AST from cursor.
'''
from clang.cindex import  TranslationUnit
import cPickle
from clang.cindex import Config
from reshaper.util import get_cursor_if
import ConfigParser
import logging, os


_CONF = Config()


class Flyweight(object):
    key2objs = {}
    def __new__(cls, *arg, **karg):
        
        if not arg:
            return super(Flyweight, cls).__new__(cls) 
        
        obj = arg[0]
        if obj is None:
            return None
        
        key = '.'.join([cls.__name__, obj.name])
        if key not in Flyweight.key2objs:
            Flyweight.key2objs[key] = super(Flyweight, cls).__new__(cls, *arg, **karg)         
        return Flyweight.key2objs[key]


class TypeKindCache(Flyweight):
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


class CursorKindCache(Flyweight):
    '''cache of CursorKind '''
    def __init__(self, kind):
        self.name = kind.name
        
    def __eq__(self, kind):
        return self.name == kind.name 
    
    def __cmp__(self, kind):
        return cmp(self.name, kind.name)


class FileCache(Flyweight):
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
        self.lexical_parent =  None
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
        
        _lexical_parent =  self._cursor.lexical_parent
        self.lexical_parent = self.create_ref_cursor_cache(_lexical_parent)
        
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
    def __init__(self, tu, keep_func= lambda _c: True):
        CursorCache.cursor2cache.clear()
        self.cursor = CursorCache(tu.cursor, keep_func)
        self.cursor.update_ref_cursors()
        self.diagnostics = []
        for diag in tu.diagnostics:
            self.diagnostics.append(DiagnosticCache(diag))
        
    def dump(self,file_path):
        cPickle.dump(self, open(file_path,'wb'), cPickle.HIGHEST_PROTOCOL)
    
    @staticmethod 
    def load(file_path):    
        return cPickle.load(open(file_path,'rb'))
        
    def get_parent(self):
        return None   
    
    

def get_tu(source, all_warnings=False, config_path = '~/.reshaper.cfg', 
           cache_folder = './'):
    """Obtain a translation unit from source and language.

    By default, the translation unit is created from source file "t.<ext>"
    where <ext> is the default file extension for the specified language. By
    default it is C, so "t.c" is the default file name.

    all_warnings is a convenience argument to enable all compiler warnings.
    """  
    
    _, filename = os.path.split(source)
    cache_path = os.path.join(cache_folder, filename + '.dump')
#     if os.path.isfile(cache_path):
#         return TUCache.load(cache_path)
        
    args = ['-x', 'c++', '-std=c++11']
 
    if all_warnings:
        args += ['-Wall', '-Wextra']

    if config_path:
        config_parser = ConfigParser.SafeConfigParser()
        config_parser.read(os.path.expanduser(config_path))
        if config_parser.has_option('Clang Options', 'include_paths'):
            include_paths = config_parser.get('Clang Options', 'include_paths')
            # pylint: disable-msg=E1103
            args += ['-I' + p for p in include_paths.split(',')]
            
        if config_parser.has_option('Clang Options', 'include_files'):
            include_files = config_parser.get('Clang Options', 'include_files')
            # pylint: disable-msg=E1103
            for ifile in include_files.split(','):
                args += ['-include', ifile]
    
    logging.debug(' '.join(args))    
    
    _tu = TranslationUnit.from_source(source, args)
    cache_tu =  TUCache(_tu)
    
    
    #cache_tu = TUCache(_tu, is_cursor_in_file_func(source))
    cache_tu.dump(cache_path)
    
    return cache_tu



def get_tu_from_text(source):
    '''copy it from util.py, just for test
    '''
    name = 't.cpp'
    args = []
    args.append('-std=c++11')

    return TUCache(TranslationUnit.from_source(name, args, 
                                               unsaved_files=[(name,
                                                              source)]))
        
        
class CursorProxy():
    def __init__(self, _cursor):
        self._cursor = _cursor
        self._source_path = _cursor.location.file
        self._hash = _cursor.hash
    
    #pickle dump and load
    def __getstate__(self):
        dic_copy = dict(self.__dict__)
        del dic_copy['_cursor'] 
        return dic_copy      
    
    def __getattr__(self, name):
        if self._cursor is None:
            self.__load_cursor()
        return getattr(self._cursor, name)
    
    def is_same_cursor(self, _cursor, _l):
        return _cursor.hash == self._hash
    
    def __load_cursor(self):
        _tu = get_tu(self._source_path)
        self._cursor = get_cursor_if(_tu, self.is_same_cursor)
        
        
