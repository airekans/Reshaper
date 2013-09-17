'''
Created on Sep 17, 2013

@author: jcchentmp
'''

from optparse import OptionParser 

def main():
    '''main function
        This script takes file name and class names as arguments.
        Directory name is optional. File directory will be used by default
    '''
    option_parser = OptionParser(usage="%prog [options] FILE CLASSNAMES [fieldnames]")
    
    option_parser.add_option("-d", "--directory", dest = "directory",\
                             type = "string", help = "set directory")
    option_parser.add_option("-f", "--fields", dest = "fields",  action = 'append',\
                             type = "string", help = "fields to encapsulate")
    
    options, args = option_parser.parse_args()
    
    if len(args) < 2:
        option_parser.error("Please input source file and class names.")
        
    file_name = args[0]
    class_names = args[1:]
    
    print options.directory
    print options.fields
    print file_name
    print class_names
    
    
if __name__ == '__main__':
    main()  