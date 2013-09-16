''' This module contains functions process the AST from cursor.
'''
from clang.cindex import  TranslationUnit
import cPickle, pickle
from clang.cindex import Config
from clang.cindex import CompilationDatabase as CDB
from reshaper.util import get_cursor_if, is_cursor_in_file_func, check_diagnostics
import ConfigParser
import logging, os
from reshaper.semantic import get_source_path_candidates, is_header


_CONF = Config()


class FlyweightBase(object):
    '''Base class for using the flyweight pattern.
       By default, it will use name as key.
       You may override get_key function to change the behavior.
     '''
    key2objs = {}
    def __new__(cls, *arg, **karg):
        
        if not arg:
            return super(FlyweightBase, cls).__new__(cls) 
        
        obj = arg[0]
        if obj is None:
            return None
        
        key = '.'.join([cls.__name__, cls.get_key(obj)])
        if key not in FlyweightBase.key2objs:
            FlyweightBase.key2objs[key] = super(FlyweightBase, cls).__new__(cls, *arg, **karg)         
        return FlyweightBase.key2objs[key]
    
    @classmethod
    def get_key(cls, obj):
        return obj.name
    
    def __getstate__(self):
        dic_copy = dict(self.__dict__)
        return dic_copy   
    
    def __init__(self, obj):
        self.name = obj.name
    
    def __eq__(self, obj):
        if not obj:
            return False
        return self.__class__.get_key(self) == self.__class__.get_key(obj)
    
    def __cmp__(self, obj):
        if not obj:
            return 1
        return cmp(self.__class__.get_key(self), self.__class__.get_key(obj))


class TypeKindCache(FlyweightBase):
    '''cache of TypeKind
    '''
    def __init__(self, type_kind):
        FlyweightBase.__init__(self, type_kind)
        self.spelling = type_kind.spelling
    

class TypeCache(object):
    '''cache of Type'''
    def __init__(self, t):
        self.kind = TypeKindCache(t.kind)


class CursorKindCache(FlyweightBase):
    '''cache of CursorKind '''
    def __init__(self, kind):
        FlyweightBase.__init__(self, kind)

class FileCache(FlyweightBase):
    ''' cache of File '''
    def __init__(self, _file):
        FlyweightBase.__init__(self, _file)

class LocationCache(FlyweightBase):
    ''' cache of Location'''
    def __init__(self, location):
        self.column = location.column
        self.line = location.line
        if location.file:
            self.file = FileCache(location.file)
        else:
            self.file = None
    
    @classmethod
    def get_key(self, location):    
        filename = location.file.name if location.file else ''    
        return '.'.join([filename, str(location.line), str(location.column)])     
   
               
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
    hash2cursor = {}
    def __init__(self, cursor, tu_file_path, is_get_children = True):
        
        
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
        self._semantic_parent =  None
        self._lexical_parent =  None
        
        self._tokens = [TokenCache(t) for t in cursor.get_tokens()]

        self._children = []
        
        self._cursor = cursor
        self.location = LocationCache(cursor.location)
        self.kind = CursorKindCache(cursor.kind)
        self._parent =  None
        
        self.hash = cursor.hash
        CursorCache.hash2cursor[self.hash] = self
        
        if is_get_children:
            for c in cursor.get_children():
                child = self.create_cursor_cache(c, is_get_children,
                                                 is_ref_cursor = False)
                if not child:
                    continue
                child.set_parent(self)
                self._children.append(child)
    
    def is_cursor_in_tu_file(self, cursor):
        return is_cursor_in_file_func(self._tu_file_path)(cursor)  
        
    def create_cursor_cache(self, cursor, is_populate_children, is_ref_cursor):
        '''is_ref_cursor means the cursor is
           declaration, definition, semantic_parent or lexical_parent '''         
        if not cursor:
            return None
        
        key = cursor.hash
        if key in CursorCache.hash2cursor:
            return CursorCache.hash2cursor[key]
        elif not self.is_cursor_in_tu_file(cursor):
            if is_ref_cursor:
                return CursorLazyLoad(cursor, self._tu_file_path)
            else:
                return None
        else:
            return CursorCache(cursor, self._tu_file_path, is_populate_children) 
    
    def update_ref_cursors(self):
        is_populate_children = False
        is_ref_cursor = True
        
        _definition = self._cursor.get_definition()
        self._definition = self.create_cursor_cache(_definition,
                                                     is_populate_children,
                                                     is_ref_cursor)
         
        _declaration = _CONF.lib.clang_getCursorReferenced(self._cursor)
        self._declaration = self.create_cursor_cache(_declaration, 
                                                     is_populate_children,
                                                     is_ref_cursor)
        
        _semantic_parent = self._cursor.semantic_parent 
        self._semantic_parent = self.create_cursor_cache(_semantic_parent, 
                                                         is_populate_children,
                                                         is_ref_cursor)
        
        _lexical_parent =  self._cursor.lexical_parent
        self._lexical_parent = self.create_cursor_cache(_lexical_parent,
                                                        is_populate_children,
                                                        is_ref_cursor)
        
        for c in self._children:
            c.update_ref_cursors()
        
    
    def __getstate__(self):
        dic_copy = dict(self.__dict__)
        del dic_copy['_tu_file_path']
        del dic_copy['_cursor'] 
        return dic_copy   
    
    def __setstate__(self, state):
        self.__dict__.update(state)
        self._cursor = None
        
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
            c.print_all(level + 1)
    
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
        
    def is_same_cursor(self, _cursor):
        return self.location == _cursor.location and \
               self.kind == _cursor.kind
               
    @property
    def semantic_parent(self):
        return self._semantic_parent
        
    @property
    def lexical_parent(self):    
        return self._lexical_parent


class CursorLazyLoad(CursorCache):
    
    def __init__(self, cursor, tu_file_path):
        CursorCache.__init__(self, cursor, tu_file_path, False)
    
    def __load_cursor(self):
        if self._cursor:
            return
        _tu = get_tu(self.location.file.name)
        self._cursor = get_cursor_if(_tu, self.is_same_cursor)
        assert(self._cursor)
    
    
    def get_children(self):
        self.__load_cursor()
        return self._cursor.get_children()
    
    def get_definition(self):
        self.__load_cursor()
        return self._cursor.get_definition()
    
    def get_declaration(self):
        self.__load_cursor()
        return self._declaration
    
    @property
    def semantic_parent(self):
        self.__load_cursor()
        return self._cursor.semantic_parent
        
    @property
    def lexical_parent(self):    
        self.__load_cursor()
        return self._cursor.lexical_parent
         
    def update_ref_cursors(self):
        pass # do nothing



class DiagnosticCache(object):
    def __init__(self, diag):
        self.spelling =  diag.spelling
        self.location = LocationCache(diag.location)


class TUCache(object):
    def __init__(self, tu, tu_path):
        CursorCache.hash2cursor.clear()
        self.cursor = CursorCache(tu.cursor, tu_path, True)
        self.cursor.update_ref_cursors()
        self.diagnostics = [DiagnosticCache(diag) for diag in tu.diagnostics]
    
    def text_dump(self, file_path):
        ''' dump with text format '''
        pickle.dump(self, open(file_path,'wb'))
        
    def dump(self,file_path):
        ''' dump with binary format, which is faster and uses less space'''
        cPickle.dump(self, open(file_path,'wb'), cPickle.HIGHEST_PROTOCOL)
    
    @staticmethod 
    def load(file_path):    
        return cPickle.load(open(file_path,'rb'))
        
    def get_parent(self):
        return None   
    
def get_ast_path(dir_name, source):
    if not dir_name:
        return source + '.ast'
    
    filename = os.path.basename(source)
    return os.path.join(dir_name, filename + '.ast')


_source2tu = {}



def _is_valid_cdb_cmds(cmds):
    return  cmds and len(cmds) == 1

def _get_cdb_cmd_for_header(cdb, cdb_path, header_path, ref_source):
      
    if ref_source:
        return cdb.getCompileCommands(os.path.join(cdb_path, ref_source))
    
    for source in get_source_path_candidates(header_path):
        cmds = cdb.getCompileCommands(os.path.join(cdb_path, source))
        if _is_valid_cdb_cmds(cmds):
            return cmds
    return None

def get_tu(source, all_warnings=False, config_path = '~/.reshaper.cfg', 
           cache_folder = '', is_from_cache_first = True,
           cdb_path = None, ref_source = None, args = []):
    """Obtain a translation unit from source and language.

    By default, the translation unit is created from source file "t.<ext>"
    where <ext> is the default file extension for the specified language. By
    default it is C, so "t.c" is the default file name.

    all_warnings is a convenience argument to enable all compiler warnings.
    """  
    
    if not os.path.isfile(source):
        logging.error('File %s dose not exist', source)
        return None
    
    full_path = os.path.abspath(source)
    if full_path in _source2tu:
        return _source2tu[full_path]
    
    if is_from_cache_first:
        cache_path = get_ast_path(cache_folder, source)
        if os.path.isfile(cache_path):
            _tu =  TUCache.load(cache_path)
            _source2tu[full_path] = _tu
            return _tu
    
    args += ['-x', 'c++', '-std=c++11']
 
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

        if config_parser.has_option('Clang Options', 'precompile_header'):
            precompile_header = config_parser.get('Clang Options', 'precompile_header')
            args += ['-include-pch', precompile_header]

    if cdb_path:
        abs_cdb_path = os.path.abspath(cdb_path)
        cdb = CDB.fromDirectory(abs_cdb_path)
        
        if is_header(source):
            cmds = _get_cdb_cmd_for_header(cdb, abs_cdb_path, source, ref_source)
        else:
            cmds = cdb.getCompileCommands(os.path.join(abs_cdb_path, source))
        
        if not _is_valid_cdb_cmds(cmds):
            raise Exception("cannot find the CDB command for %s" % source)

        filter_options = ['clang', 'clang++', '-MMD', '-MP']
        args += [arg for arg in cmds[0].arguments if arg not in filter_options]

    logging.debug(' '.join(args))
    
    _tu = TranslationUnit.from_source(source, args)
    
    # cache_tu = TUCache(_tu, source)
    # _source2tu[full_path] = cache_tu
    
    return _tu

def save_ast(file_path, _dir=None , is_readable=False, \
             config_path=None, cdb_path=None, ref_source = None):
    
    _tu = get_tu(file_path, is_from_cache_first = False,
                 cdb_path = cdb_path,
                 config_path = config_path,
                 ref_source = ref_source)
    
    if not _tu:
        print "unable to load %s" % file_path
        return False
    
    check_diagnostics(_tu.diagnostics)
        
    cache_path = get_ast_path(_dir, file_path)
    
    print 'Saving ast of %s to %s' % (file_path, cache_path)
        
    if is_readable:
        _tu.text_dump(cache_path)
    else:
        _tu.dump(cache_path)
        
    return True


