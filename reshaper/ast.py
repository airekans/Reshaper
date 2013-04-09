''' This module contains functions process the AST from cursor.
'''

from clang.cindex import Cursor


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

    def preprocess_ast(cursor, parent):
        cursor.ast_parent = parent
        cursor.ast_children = []

        for child in cursor.get_children():
            cursor.ast_children.append(child)
            preprocess_ast(child, cursor)

    preprocess_ast(cursor, None)
    return cursor
    
        