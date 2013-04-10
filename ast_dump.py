#!/usr/bin/env python

from reshaper.util import get_tu, walk_ast
from clang.cindex import TranslationUnit
from optparse import OptionParser
import sys

def print_cursor(cursor, level):
    prefix = "**" * level

    lexical_parent = cursor.lexical_parent
    semantic_parent = cursor.semantic_parent
    print prefix + "spelling:", cursor.spelling
    print prefix + "displayname:", cursor.displayname
    print prefix + "kind:", cursor.kind.name

    if cursor.type is not None:
        print prefix + "type kind:", cursor.type.kind.name
    
    print prefix + "is_definition:", cursor.is_definition()
    print prefix + "lexical_parent:", \
        lexical_parent.spelling if lexical_parent is not None else None
    print prefix + "semantic_parent:", \
         semantic_parent.spelling if semantic_parent is not None else None
    print 

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'invalid number arguments'
        sys.exit(1)

    tu = get_tu(sys.argv[1])
    if not tu:
        print "unable to load input"
        sys.exit(1)

    walk_ast(tu, print_cursor)
    

    
