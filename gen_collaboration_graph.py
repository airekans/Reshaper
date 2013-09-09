'''
Created on May 30, 2013

@author: liangzhao
'''
from optparse import OptionParser
import os, sys
from reshaper.option import setup_options
from reshaper.ast import get_tu
from reshaper.dot_gen_util import gen_class_collaboration_graph

def main(argv = sys.argv[1:]):
    ''' main '''
    option_parser = OptionParser(usage = "%prog [options] classes") 
    
    option_parser.add_option("-f", "--file", dest = "file", \
                             type="string", default='', \
                             help = "input file path ")
    option_parser.add_option("-d", "--dir", dest = "dir", \
                             type="string", default='', \
                             help = "only show classes defined in this dir")
    option_parser.add_option("-s", "--show_functions", dest = "show_func", \
                             action="store_true", \
                             help = "show function names")
    
    setup_options(option_parser)
    (options, args) = option_parser.parse_args(args = argv)
    
    file_path = options.file
    
    if not file_path:
        option_parser.error('-f option is not set')
        
    if not os.path.isfile(file_path):
        option_parser.error('file %s dose not exist' % file_path)
        
    class_names = args
    if not class_names:
        option_parser.error('Please input class names')
        
    tu_source = get_tu(os.path.abspath(file_path),
                       config_path = options.config,
                       cdb_path = options.cdb_path)
    
    print gen_class_collaboration_graph(tu_source, class_names, 
                                        options.dir, options.show_func)

if __name__ == '__main__':
    main()
        
        