'''
Created on Apr 7, 2013

@author: liangzhao



'''

from reshaper import class_serializer as cs
from optparse import OptionParser 
from reshaper import header_util as hu, util

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

def _main():
    ''' main function '''
    option_parser = OptionParser(usage="%prog [options] FILE [CLASSNAMES]")
    option_parser.add_option("-e", "--equal", dest="equal", \
                             action="store_true", help="generate operator==")
    option_parser.add_option("-s", "--serialize", dest="serialize", \
                             action="store_true", \
                             help="generate serialize operator")
    options, args = option_parser.parse_args()
    
    if len(args) < 1:
        print "Please input source file and class name."
        import sys
        sys.exit(1)
    header_path = args[0]
    
    if len(args) == 1:
        tu_ = util.get_tu(header_path)
        class_names = hu.get_all_class_names(tu_, header_path)
    else:
        class_names = args[1:]
    
    set_all_true_if_no_option(options)
    
    for class_name in class_names:
        if options.equal:
            print cs.generate_eq_op_code(header_path, class_name)
            print
        if options.serialize:
            print cs.generate_serialize_code(header_path, class_name)
            print
        print 
            
if __name__ == '__main__':
    _main()    
    
    
    
    
    
    

    
    
   
     