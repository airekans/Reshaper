''' This module contains functions process the AST from cursor.
'''

from clang.cindex import Cursor
import pickle

class CacheCursor(object):
    def __init__(self, cursor, keep_func):
        self.spelling = cursor.spelling 
        self.displayname = cursor.displayname
        self.kind = cursor.kind.name
        self._children = []
        for c in cursor.get_children():
            if not keep_func(c):
                continue
            self._children.append(CacheCursor(c, keep_func))
    def dump(self,file_path):
        pickle.dump(self, open(file_path,'w'))
    
    @staticmethod 
    def load(file_path):    
        return pickle.load(open(file_path))
    
    def print_all(self, level =0):
        prefix = "**" * level
        print prefix + "spelling:", self.spelling
        print prefix + "displayname:", self.displayname
        print prefix + "kind:", self.kind
        for c in self._children:
            c.print_all(level+1)

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
    
        