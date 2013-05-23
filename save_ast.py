#!/usr/bin/env python

from reshaper.ast import save_ast
from optparse import OptionParser
from reshaper.option import setup_options


def main():
   
    option_parser = OptionParser(usage = "%prog [options] files") 
    setup_options(option_parser)
    option_parser.add_option("-d", "--dir", dest = "dir", \
                             type="string", default='', \
                             help = "destination dir to put output file, by default it is the same dir as input")
    option_parser.add_option("-r", "--readable", dest = "readable", \
                             action="store_true", \
                             help = "dump with readable format (slow)")
    
    option_parser.add_option("-s", "--ref_source", dest = "ref_source", \
                             type="string", default='', \
                             help = "reference source file (only used when input is a header file)")
    
    
    (options, args) = option_parser.parse_args()
       
    if len(args) < 1:
        option_parser.error('Please input files to parse')
    
    for file_path in args:     
        try:
            save_ast(file_path, options.dir, options.readable, \
                     config_path= options.config,
                     cdb_path = options.cdb_path,
                     ref_source = options.ref_source)
        except:
            print "Can't parse %s" % file_path 
        
        
if __name__ == '__main__':
    main()
    
