'''
Created on May 30, 2013

@author: liangzhao
'''
from optparse import OptionParser
import os


def main():
    ''' main '''
    option_parser = OptionParser(usage = "%prog [options] classes") 
    
    option_parser.add_option("-f", "--file", dest = "file", \
                             type="string", default='', \
                             help = "input file path ")
    
    
    (options, args) = option_parser.parse_args()
    
    file_path = options.file
    if not os.path.isfile(file_path):
        option_parser.error('file %s dose not exist' % file_path)
        
    class_names = args
    if not class_names:
        option_parser.error('Please input class names')

if __name__ == '__main__':
    main()
        
        