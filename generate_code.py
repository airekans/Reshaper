'''
Created on Apr 7, 2013

@author: liangzhao
'''

from reshaper import code_generator as cg
from optparse import OptionParser 


def set_all_true_if_no_option(opts):
    '''
    if no option set, take all options as true
    '''
    has_option = False
    for _, value in vars(opts).iteritems():
        if value:
            has_option = True
    
    if has_option:
        return
    
    for attr, value in vars(opts).iteritems():
        setattr(opts, attr, True)
        
if __name__ == '__main__':
    
    option_parser = OptionParser(usage = "%prog [options] FILE CLASSNAME")
    option_parser.add_option("-e", "--equal", dest = "equal",
                             action="store_true",
                             help = "generate operator==")
    
    option_parser.add_option("-s", "--serialize", dest = "serialize",
                             action="store_true",
                             help = "generate serialize operator")
    
    (options, args) = option_parser.parse_args()
        
    if len(args) != 2:
        print "Please input source file and class name."
        import sys
        sys.exit(1)
    
    header_path, class_name = args     
    set_all_true_if_no_option(options)
    
    if options.equal:
        print cg.generate_eq_op_code(header_path, class_name)
    
    if options.serialize:
        print cg.generate_serialize_code(header_path, class_name)    
    
    
    
    
    
    

    
    
   
     