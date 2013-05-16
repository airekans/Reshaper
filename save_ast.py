#!/usr/bin/env python

from reshaper.ast import save_ast
from optparse import OptionParser
from reshaper.option import setup_options
import sys
import os


def main():
   
    option_parser = OptionParser(usage = "%prog [options] files") 
    setup_options(option_parser)
    option_parser.add_option("-d", "--dir", dest = "dir", \
                             type="string", default='', \
                             help = "max level to print")
    option_parser.add_option("-r", "--readable", dest = "readable", \
                             action="store_true", \
                             help = "dump with readable format (slow)")
    (options, args) = option_parser.parse_args()
       
    if len(args) < 1:
        option_parser.error('Please input files to parse')
    
    for file_path in args:     
        save_ast(file_path, options.dir, options.readable)
        
        
if __name__ == '__main__':
    main()
    
