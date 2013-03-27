import sys, os
from clang.cindex import *
from util import get_tu
from util import get_cursor

file_types = ('.cpp', '.c', '.cc')

'''Get Cursors through tu or cursor according to its spelling and displayname'''
def getCursorsWithParent(source, spelling):
    children = []
    cursors = []
    if isinstance(source, Cursor):
        children = source.get_children()
    else:
        # Assume TU
        children = source.cursor.get_children()

    for cursor in children:
        if cursor is not None and isinstance(cursor, Cursor):
             cursor.parent = source
        if cursor.is_definition():
            if cursor.spelling == spelling:
                cursors.append(cursor)
        else:
            if spelling in cursor.displayname :
                cursors.append(cursor)
        # Recurse into children.
        cursors.extend( getCursorsWithParent(cursor, spelling))
    return cursors

'''Scan directory recursivly to get files with file_types'''
def scanDirParseFiles(dir, parseFileCB, ref):
    for root, dirs, files in os.walk(dir):
        for file in files:
            name, type = os.path.splitext(file)
            if type in file_types:
                parseFileCB(os.path.join(root, file), ref)
        for subDir in dirs:
            scanDirParseFiles(os.path.join(root, subDir), parseFileCB, ref)

'''Get specific cursor by line and column'''
def getCursorForLocation(tu, spelling, line, column):
    cursors2 = getCursorsWithParent(tu, spelling)
    for cursor in cursors2:
        if cursor.kind == CursorKind.CALL_EXPR and len(list(cursor.get_children())) > 0:
            continue
        if column is not None:
            if cursor.location.line == line and cursor.location.column == column:
                return cursor
        else:
            if cursor.location.line == line:
                return cursor
    return None

'''find call func'''
def getCallFunc(source):
   # assert isinstance(source, Cursor)
    if not isinstance(source, Cursor) or source.parent is None or not isinstance(source.parent, Cursor):
        return None
    elif source.parent.type.kind == TypeKind.FUNCTIONPROTO:
        return source.parent
    else:
        return getCallFunc(source.parent)

    
