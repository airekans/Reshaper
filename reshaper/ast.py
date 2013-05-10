''' This module contains functions process the AST from cursor.
'''
from clang.cindex import  TranslationUnit
import cPickle, pickle
from clang.cindex import Config
from reshaper.util import get_cursor_if, is_cursor_in_file_func
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
    
    def __init__(self, obj):
        self.name = obj.name
    
    def __eq__(self, obj):
        if not obj:
            return False
        return self.name == obj.name
    
    def __cmp__(self, obj):
        if not obj:
            return 1
        return cmp(self.name, obj.name)


class TypeKindCache(Flyweight):
    '''cache of TypeKind
    '''
    def __init__(self, type_kind):
        Flyweight.__init__(self, type_kind)
        self.spelling = type_kind.spelling
    

class TypeCache(object):
    '''cache of Type'''
    def __init__(self, t):
        self.kind = TypeKindCache(t.kind)


class CursorKindCache(Flyweight):
    '''cache of CursorKind '''
    def __init__(self, kind):
        Flyweight.__init__(self, kind)

class FileCache(Flyweight):
    ''' cache of File '''
    def __init__(self, _file):
        Flyweight.__init__(self, _file)

class LocationCache(object):
    ''' cache of Location'''
    def __init__(self, location):
        self.column = location.column
        self.line = location.line
        if location.file:
            self.file = FileCache(location.file)
        else:
            self.file = None
    def __eq__(self, location):
        return self.file == location.file and \
               self.line == location.line and \
               self.column == location.column
    def __cmp__(self, location):
        return cmp( (self.file, self.line, self.column),
                    (location.file, location.line, location.column)
                  )
               
class ExtentCache(object):
    '''cache of Extent'''
    def __init__(self, extent):
        self.start = LocationCache(extent.start)
        self.end = LocationCache(extent.end)

class TokenCache(object):
    def __init__(self, token):
        self.extent = ExtentCache(token.extent)
        self.spelling =  token.spelling


class CursorProxy(object):
    hash2cursor = {}
    
    def __init__(self, _cursor):
        self._cursor = _cursor
        self.location = LocationCache(_cursor.location)
        self.kind = CursorKindCache(_cursor.kind)
        self._parent =  None
        
        self.hash = _cursor.hash
        CursorProxy.hash2cursor[self.hash] = self
    
    #pickle dump and load
    def __getstate__(self):
        dic_copy = dict(self.__dict__)
        del dic_copy['_cursor'] 
        return dic_copy      
    
    def __setstate__(self, state):
        self.__dict__.update(state)
        _tu = get_tu(self.location.file.name)
        self._cursor = get_cursor_if(_tu, self.is_same_cursor)
        assert(self._cursor)
    
    def __getattr__(self, name):           
        return getattr(self._cursor, name)
    
    def is_same_cursor(self, _cursor):
        return self.location == _cursor.location and \
               self.kind == _cursor.kind 
        
    def get_parent(self):
        return self._parent
    
    def set_parent(self, parent):
        self._parent =  parent
        
    def update_ref_cursors(self):
        pass # do nothing

class CursorCache(CursorProxy):
    ''' Cache for Cursor'''

    def __init__(self, cursor, tu_file_path, is_get_children = True):
        CursorProxy.__init__(self,cursor)
        
        self._tu_file_path = tu_file_path
        self._cursor = cursor
         
        self.spelling = cursor.spelling 
        self.displayname = cursor.displayname
        self.usr = cursor.get_usr()
        self._is_definition = cursor.is_definition()
        self.location = LocationCache(cursor.location)
        self.type = TypeCache(cursor.type)
        
        self._usr = cursor.get_usr()
        self._definition = None
        self._declaration = None
        self.semantic_parent =  None
        self.lexical_parent =  None
        
        self._tokens = []
        for t in cursor.get_tokens():
            self._tokens.append(TokenCache(t))

        self._children = []
        
        if is_get_children:
            for c in cursor.get_children():
                if not self.is_cursor_in_tu_file(c):
                    child = CursorProxy(c)
                else:
                    child = CursorCache(c, tu_file_path, is_get_children)
                child.set_parent(self)
                self._children.append(child)
        
    
    def is_cursor_in_tu_file(self, c):
        return is_cursor_in_file_func(self._tu_file_path)(c)    
        
    def create_ref_cursor_cache(self, ref_cursor):
                
        if not ref_cursor:
            return None
        
        key = ref_cursor.hash
        if key in CursorProxy.hash2cursor:
            return CursorProxy.hash2cursor[key]
        else:
            #not keep child
            return CursorCache(ref_cursor, self._tu_file_path, False)
    
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
        del dic_copy['_tu_file_path']
        del dic_copy['_cursor'] 
        return dic_copy   
    
    def __setstate__(self, state):
        self.__dict__.update(state)
        
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
    
    def __getattr__(self, name):
        return object.__getattribute__(self, name)
    

class DiagnosticCache(object):
    def __init__(self, diag):
        self.spelling =  diag.spelling


class TUCache(object):
    def __init__(self, tu, tu_path):
        CursorCache.hash2cursor.clear()
        self.cursor = CursorCache(tu.cursor, tu_path, True)
        self.cursor.update_ref_cursors()
        self.diagnostics = []
        for diag in tu.diagnostics:
            self.diagnostics.append(DiagnosticCache(diag))
    
    def readable_dump(self, file_path):
        pickle.dump(self, open(file_path,'wb'))
        
    def dump(self,file_path):
        cPickle.dump(self, open(file_path,'wb'), cPickle.HIGHEST_PROTOCOL)
    
    @staticmethod 
    def load(file_path):    
        return cPickle.load(open(file_path,'rb'))
        
    def get_parent(self):
        return None   
    
def get_ast_path(dir_name, source):
    if not dir_name:
        return source + '.ast'
    
    _, filename = os.path.split(source)
    return os.path.join(dir_name, filename + '.ast')


_source2tu = {}

def get_tu(source, all_warnings=False, config_path = '~/.reshaper.cfg', 
           cache_folder = '', is_from_cache_first = True):
    """Obtain a translation unit from source and language.

    By default, the translation unit is created from source file "t.<ext>"
    where <ext> is the default file extension for the specified language. By
    default it is C, so "t.c" is the default file name.

    all_warnings is a convenience argument to enable all compiler warnings.
    """  
    
    #if _source2tu
    
    if is_from_cache_first:
        cache_path = get_ast_path(cache_folder, source)
        if os.path.isfile(cache_path):
            return TUCache.load(cache_path)
        
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
    #cache_tu =  TUCache(_tu)
    
    cache_tu = TUCache(_tu, source)
    
    
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
        
