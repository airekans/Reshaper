'''
Created on Sep 11, 2013

@author: jcchentmp
'''

import sys, os.path
from optparse import OptionParser 
from reshaper.option import setup_options
import reshaper.transform as trs

def main(argv = sys.argv[1:]):
    '''main function
        This script takes file name and class names as arguments.
        Directory name is optional. File directory will be used by default
    '''
    option_parser = OptionParser(usage="%prog [options] FILE CLASSNAMES")
    setup_options(option_parser)
    
    option_parser.add_option("-d", "--directory", dest = "directory", \
                             action = "store_true", help = "set directory")
    
    options, args = option_parser.parse_args(args = argv)
    
    if len(args) < 2:
        option_parser.error("Please input source file and class names.")
        
    file_name = args[0]
    class_names = args[1:]
    
    if options.directory:
        directory = options.directory
    else:
        directory = os.path.dirname(file_name)
    
    trs.transform(file_name, class_names, directory)
    
    
if __name__ == '__main__':
    main()  
    