#!/usr/bin/env python

from util import walk_ast
from clang.cindex import TranslationUnit
from clang.cindex import TypeKind
from clang.cindex import Config
from optparse import OptionParser

conf = Config()

def print_cursor(cursor, level):
    prefix = "**" * level
    print prefix + "spelling:", cursor.spelling
    print prefix + "displayname:", cursor.displayname
    print prefix + "kind:", cursor.kind.name
    print prefix + "is_definition:", cursor.is_definition()
    print prefix + "location:", cursor.location
    print prefix + "USR:", cursor.get_usr()
    refCursor = conf.lib.clang_getCursorReferenced(cursor)
    if refCursor:
        print prefix + "refCursor USR", refCursor.get_usr()
        print prefix + "refCursor location", refCursor.location
    print


if __name__ == '__main__':
    parser = OptionParser("usage: %prog [options] {filename} [clang-args*]")
    (opts, args) = parser.parse_args()

    if len(args) == 0:
        parser.error('invalid number arguments')

    tu = TranslationUnit.from_source(args[0], ['-std=c++11'])

    if not tu:
        parser.error("unable to load input")

    print len(tu.diagnostics)
    for d in tu.diagnostics:
        print d

    walk_ast(tu, print_cursor)
    

    
