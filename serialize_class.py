'''
Created on Apr 7, 2013

@author: liangzhao



'''

from reshaper import class_serializer as cs
from optparse import OptionParser 
from reshaper import header_util as hu, util
import sys

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
        option_parser.error("Please input source file and class name.")
        
    header_path = args[0]

    tu_ = util.get_tu(header_path)
    if util.check_diagnostics(tu_.diagnostics):
        sys.exit(1)
    if len(args) == 1:
        classes = hu.get_all_class_cursors(tu_)
    else:
        classes = hu.get_classes_with_names(tu_, args[1:])

    tmp_classes = []
    for cls in classes:
        if cls.is_definition():
            tmp_classes.append(cls)
        else:
            print "class %s is not defined and will not be generated" % cls.spelling
        
    classes = tmp_classes
        
    set_all_true_if_no_option(options)
    
    def do_print(code, class_name, function_name):
        if not code:
            print '%s not generated for %s' % (function_name, class_name)
        else:
            print code
        print
    
    for cls in classes:
        if options.equal:
            do_print(cs.generate_eq_op_code(cls), cls.spelling, 'operator==')
            
        if options.serialize:
            do_print(cs.generate_serialize_code(cls), cls.spelling, 'Serialization')
         
if __name__ == '__main__':
    _main()    
    
    
    
    
    
    

    
    
   
     