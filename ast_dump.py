#!/usr/bin/env python

from reshaper.util import get_tu, walk_ast
from clang.cindex import TranslationUnit
from optparse import OptionParser
import sys, os

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
    option_parser = OptionParser(usage = "%prog [options] files") 
    option_parser.add_option("-l", "--level", dest = "level",
                             type="int",\
                             help = "max level to print")
    option_parser.add_option("-a", "--all", dest = "all",
                             action="store_true",
                             help = "walk all cursor nodes including\
                                     the ones not defined in this file")
    
    (options, args) = option_parser.parse_args()
    
    if len(args) < 1:
        print 'Please input files to parse'
        sys.exit(1)
          
    
    FILE_PATHS = set([os.path.abspath(path) for path in args])

    def can_visit_cursor_func(cursor, level):
        can_visit =  True
        if options.level is not None:
            can_visit = (level <= options.level)
        if not options.all :
            cursor_file = cursor.location.file
            if cursor_file:
                can_visit = can_visit and \
                                os.path.abspath(cursor_file.name) in FILE_PATHS
        return can_visit
        
    for file_path in args:     
        tu = get_tu(file_path)
        if not tu:
            print "unable to load %s" % file_path
            sys.exit(1)

        error_num = len(tu.diagnostics)
        if error_num > 0:
            print "Source file has the following errors(%d):" % error_num
            for diag in tu.diagnostics:
                print diag.spelling

            sys.exit(1)
    
        walk_ast(tu, print_cursor, can_visit_cursor_func)
    

    
