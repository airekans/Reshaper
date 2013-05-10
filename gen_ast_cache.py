#!/usr/bin/env python

from reshaper.ast import get_tu, get_ast_path
from optparse import OptionParser
import sys
import os


def main():
   
    option_parser = OptionParser(usage = "%prog [options] files") 
    option_parser.add_option("-d", "--dir", dest = "dir", \
                             type="string", default='', \
                             help = "max level to print")
    option_parser.add_option("-r", "--readable", dest = "readable", \
                             action="store_true", default='False', \
                             help = "dump with readable format (slow)")
    (options, args) = option_parser.parse_args()
       
    if len(args) < 1:
        option_parser.error('Please input files to parse')
    
    for file_path in args:     
        _tu = get_tu(file_path, is_from_cache_first = False)
        if not _tu:
            print "unable to load %s" % file_path
            sys.exit(1)
            
        cache_path = get_ast_path(options.dir, file_path)
            
        if options.readable:
            _tu.readable_dump(cache_path)
        else:
            _tu.dump(cache_path)
        
if __name__ == '__main__':
    main()
    
