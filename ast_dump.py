#!/usr/bin/env python

from reshaper.ast import get_tu
from reshaper.util import walk_ast, is_cursor_in_file_func
from reshaper.util import check_diagnostics
from reshaper.option import setup_options
from optparse import OptionParser
import sys
from functools import partial
from xml.sax.saxutils import escape



SPACE = '    '

class XMLPrinter(object):
    def __init__(self):
        self._level = -1
        self._stack = []
    
    def print_tag(self, level, tag, attr_label, attr):
        
        if self._stack:
            for _i in range(0, self._level-level+1):
                end_tag = self._stack.pop()
                print end_tag
        
        attr_str = ''
        if attr_label:
            attr_str = ' %s="%s"' % (attr_label, escape(attr))
            
        start_tag =  SPACE * level + '<%s%s>' % (tag, attr_str)
        print start_tag
        end_tag   = SPACE * level + '</%s>' % tag
        self._stack.append(end_tag)  
               
        self._level = level
        
    def print_attr(self, level, name, value):
        print SPACE * (level+1) + '<%s>%s</%s>' % (name, value, name)
        
    def print_remaining_end_tags(self):
        while self._stack:
            end_tag = self._stack.pop()
            print end_tag
        

_xml_printer = XMLPrinter()        


def print_tag(level, tag, is_xml, attr_label='', attr = ''):
    if is_xml:
        _xml_printer.print_tag(level, tag, attr_label, attr)
    else:
        attr_str = ''
        if attr_label:
            attr_str = ': %s=%s' % (attr_label, attr)
        print '****' * level + '%s%s' % (tag, attr_str)

def print_attr(level, name, value, is_xml):
    if is_xml:
        value = escape(str(value))
        _xml_printer.print_attr(level, name, value)
    else:
        print '****' * (level+1) + name + ':', value
        

def print_cursor(cursor, level, is_print_ref = False, is_xml = False):
    
   
    
    print_func = lambda level, name, value: print_attr(level, name, value, is_xml) 
    
    if cursor is None:
        print_tag(level,'cursor', is_xml) 
        return
    else:
        print_tag(level, 'cursor', is_xml, "displayname", cursor.displayname)
 
    print_func(level, "spelling", cursor.spelling)
    print_func(level, "kind", cursor.kind.name)
    print_func(level, "usr", cursor.get_usr())
    print_func(level, "hash", cursor.hash)
    if cursor.location.file:
        print_func(level,  "file", "%s:%d:%d" % (cursor.location.file.name, \
                                           cursor.location.line, \
                                           cursor.location.column))
    
    if cursor.type is not None:
        print_func(level, "type_kind", cursor.type.kind.name)
    
    print_func(level, "is_definition", cursor.is_definition())
    
    if is_print_ref:   
        lexical_parent = cursor.lexical_parent
        semantic_parent = cursor.semantic_parent
        declaration = cursor.get_declaration()
        definition = cursor.get_definition()
    
        print_tag(level+1, 'semantic_parent', is_xml)
        print_cursor(semantic_parent, level+2, False, is_xml)
        
        print_tag(level+1,  "lexical_parent", is_xml)
        print_cursor(lexical_parent, level+2, False, is_xml)
        
        print_tag(level+1,   "definition", is_xml)
        print_cursor(definition, level+2, False, is_xml)
        
        print_tag(level+1, "declaration", is_xml)
        print_cursor(declaration, level+2, False, is_xml)
        
    
    

def main():
    option_parser = OptionParser(usage = "%prog [options] files")
    setup_options(option_parser)
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
    
    option_parser.add_option("-x", "--xml", dest = "xml",
                             action="store_true",
                             help = "print with xml format")
    
    (options, args) = option_parser.parse_args()
       
    if len(args) < 1:
        option_parser.error('Please input files to parse')
    
    def can_visit_cursor_func(cursor, level, path):
        can_visit =  True
        if options.level is not None:
            can_visit = (level <= options.level)
        if not options.all:
            can_visit = can_visit and is_cursor_in_file_func(path)(cursor, level)
        return can_visit
        
    for file_path in args:     
        _tu = get_tu(file_path, config_path= options.config,
                     cdb_path = options.cdb_path)
        if not _tu:
            print "unable to load %s" % file_path
            sys.exit(1)
            
        error_num = len(_tu.diagnostics)

        check_diagnostics(_tu.diagnostics)

        walk_ast(_tu,
                  partial(print_cursor, is_print_ref =  options.reference,
                                        is_xml = options.xml),
                  partial(can_visit_cursor_func, path = file_path))

        if options.xml:
            _xml_printer.print_remaining_end_tags()

        
        
if __name__ == '__main__':
    main()
    
