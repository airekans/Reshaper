#!/usr/bin/env python

from util import walk_ast
from clang.cindex import TranslationUnit
from optparse import OptionParser


def print_cursor(cursor, level):
    prefix = "**" * level
    print prefix + "spelling:", cursor.spelling
    print prefix + "displayname:", cursor.displayname
    print prefix + "kind:", cursor.kind.name
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
    

    
