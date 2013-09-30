'''
Created on Apr 7, 2013

@author: liangzhao
'''

from reshaper import class_serializer as cs
from optparse import OptionParser 
from reshaper import semantic as sem, util
from reshaper.option import setup_options
import sys
from reshaper.ast import get_tu

def set_all_true_if_no_bool_option(opts):
    '''
    if no bool option set, take all bool options as true
    '''
    has_bool_option = False
    for _, value in vars(opts).iteritems():
        if value and isinstance(value, bool):
            has_bool_option = True
    
    if has_bool_option:
        return
    
    for attr, value in vars(opts).iteritems():
        setattr(opts, attr, True)

def _main(argv = sys.argv[1:]):
    ''' main function '''
    option_parser = OptionParser(usage="%prog [options] FILE [CLASSNAMES]")
    setup_options(option_parser)
    option_parser.add_option("-e", "--equal", dest="equal", \
                             action="store_true", help="generate operator==")
    option_parser.add_option("-s", "--serialize", dest="serialize", \
                             action="store_true", \
                             help="generate serialize operator")
    
    
    options, args = option_parser.parse_args(args = argv)
    
    if len(args) < 1:
        option_parser.error("Please input source file and class name.")
        
    header_path = args[0]

    tu_ = get_tu(header_path, 
                 config_path= options.config,
                 cdb_path = options.cdb_path)
    
         
    util.check_diagnostics(tu_.diagnostics)
    
    if len(args) == 1:
        classes = sem.get_all_class_cursors(tu_, header_path)
    else:
        classes = sem.get_classes_with_names(tu_, args[1:])

    tmp_classes = []
    for cls in classes:
        if cls.is_definition():
            tmp_classes.append(cls)
        else:
            sys.stderr.write("class %s is not defined and will not be generated\n" % cls.spelling)
        
    classes = tmp_classes
        
    set_all_true_if_no_bool_option(options)
    
    def do_print(code, class_name, function_name):
        if not code:
            sys.stderr.write('%s not generated for %s\n' % (function_name, class_name))
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