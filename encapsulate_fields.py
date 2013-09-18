'''
Created on Sep 11, 2013

@author: jcchentmp
'''

import sys, os.path
from optparse import OptionParser 
from reshaper.option import setup_options
import reshaper.encapsulator as encap

def main(argv = sys.argv[1:]):
    '''main function
        This script takes file name and class names as arguments.
        Directory name is optional. File directory will be used by default
    '''
    option_parser = OptionParser(usage="%prog [-d dir] [-f field1,field2...] FILE CLASSNAMES")
    setup_options(option_parser)
    
    option_parser.add_option("-d", "--directory", dest = "directory",
                             help = "set directory")
    option_parser.add_option("-f", "--field", dest = "fields", 
                             help = "set fields to encapsulate")
    option_parser.add_option("-i", "--in-place", action = "store_true", \
            dest = "inplace", help = \
            "if given, will checkout files and encapsulate fields."
            "or else, will generator new files suffixed with .bak.")
    
    options, args = option_parser.parse_args(args = argv)
    
    if len(args) < 2:
        option_parser.error("Please input source file and class names.")
        
    file_name = args[0]
    class_names = args[1:]
    
    if options.directory:
        directory = options.directory
    else:
        directory = os.path.dirname(file_name)
    
    if options.fields:
        fields = options.fields.split(',')
        fields = [field.strip() for field in fields]
    else:
        fields = None
    
    encap.encapsulate(file_name, class_names, directory, fields, options.inplace)
    
    
if __name__ == '__main__':
    main()  
    