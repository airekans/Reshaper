import sys, os
from clang.cindex import TranslationUnit
from clang.cindex import Cursor
from clang.cindex import CursorKind
from clang.cindex import TypeKind
from clang.cindex import Config

file_types = ('.cpp', '.c', '.cc')
conf = Config()

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
def scanDirParseFiles(dir, parseFileCB):
    for root, dirs, files in os.walk(dir):
        for file in files:
            name, type = os.path.splitext(file)
            if type in file_types:
                parseFileCB(os.path.join(root, file))
        for subDir in dirs:
            scanDirParseFiles(os.path.join(root, subDir), parseFileCB)

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

    
'''check diagnostics warning'''
def checkDiagnostics(diagnostics):
    hasDiagnostics = False
    for dia in diagnostics:
        hasDiagnostics = True
        print dia
    return hasDiagnostics

'''get declaration cursor of ref'''
def getDeclarationCursor(cursor):
    assert(isinstance(cursor, Cursor))
    decCursor = conf.lib.clang_getCursorReferenced(cursor)
    if isinstance(decCursor, Cursor):
        return decCursor
    return None

'''get Cursor semantic parent information'''
def getDeclSemanticParent(cursor):
    assert(isinstance(cursor, Cursor))
    decCursor = getDeclarationCursor(cursor)
    if not isinstance(decCursor, Cursor) or decCursor.semantic_parent is None:
        return None
    return decCursor.semantic_parent
