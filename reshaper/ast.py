''' This module contains functions process the AST from cursor.
'''

from clang.cindex import Cursor


class StaticCursor(object):
    """ StaticCursor is a cursor that will not change its tree structure
    after the file is change.
    So you can use it to travese the AST easily with StaticCursor.

    Note that if you get cursor by using the native API of cindex,
    the return cursor will be Cursor instead of StaticCursor,
    so this operation will invalidate the static AST.
    
    """
    
    def __init__(self, cursor, parent = None):
        """
        """

        self.__cursor = cursor
        self.__parent = parent
        self.__children = [StaticCursor(child, self)
                           for child in cursor.get_children()]
        
    def get_parent(self):
        return self.__parent

    def get_children(self):
        """
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
    
        