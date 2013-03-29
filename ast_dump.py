#!/usr/bin/env python

from reshaper.util import walk_ast
from clang.cindex import TranslationUnit
from optparse import OptionParser


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
    parser = OptionParser("usage: %prog [options] {filename} [clang-args*]")
    (opts, args) = parser.parse_args()

    if len(args) == 0:
        parser.error('invalid number arguments')

    tu = TranslationUnit.from_source(args[0], ['-std=c++11'])
    if not tu:
        parser.error("unable to load input")

    walk_ast(tu, print_cursor)
    

    
