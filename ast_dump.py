#!/usr/bin/env python

from reshaper.util import get_tu, walk_ast, is_curor_in_file
from optparse import OptionParser
import sys
from functools import partial
from reshaper.semantic import get_declaration_cursor

def print_cursor(cursor, level, is_print_ref = False):
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
    
    if is_print_ref:
        ref_cursor = get_declaration_cursor(cursor)
        if not ref_cursor or ref_cursor == cursor:
            return
        print prefix + "reference:"
        print_cursor(ref_cursor, level+1, is_print_ref)

if __name__ == '__main__':
    
    option_parser = OptionParser(usage = "%prog [options] files") 
    option_parser.add_option("-l", "--level", dest = "level",
                             type="int",\
                             help = "max level to print")
    option_parser.add_option("-a", "--all", dest = "all",
                             action="store_true",
                             help = "walk all cursor nodes including\
                                     the ones not defined in this file")
    
    option_parser.add_option("-r", "--reference", dest = "reference",
                             action="store_true",
                             help = "print info of referenced cursor")
    
    (options, args) = option_parser.parse_args()
       
    if len(args) < 1:
        print 'Please input files to parse'
        sys.exit(1)
          
    
    
    def can_visit_cursor_func(cursor, level, path):
        can_visit =  True
        if options.level is not None:
            can_visit = (level <= options.level)
        if not options.all :
            can_visit = can_visit and is_curor_in_file(cursor, path)
        return can_visit
        
    for file_path in args:     
        tu = get_tu(file_path)
        if not tu:
            print "unable to load %s" % file_path
            sys.exit(1)
    
        walk_ast(tu, partial(print_cursor, is_print_ref =  options.reference), \
                     partial(can_visit_cursor_func, path = file_path))
    

    
