#! /usr/bin/env python

""" This tool is used to extract interface from a source/header file.
The result will be output to stdout.

Usage: extract_interface.py class.cpp class_name

"""
import sys
import os
from reshaper.ast import get_tu
from reshaper.util import get_cursor_if
from reshaper.extract import extract_interface
from reshaper.option import setup_options
from reshaper import semantic
from optparse import OptionParser
from functools import partial


def parse_options(argv):
    """ parse the command line options and arguments and returns them
    """

    option_parser = OptionParser(usage = "%prog [options] FILE CLASSNAME",)
    setup_options(option_parser)
    option_parser.add_option("-m", "--methods", dest = "methods",
                             type = "string",
                             help = "Names of methods you want to extract")
    option_parser.add_option("--from-function", dest = "from_function",
                             type = "string",
                             help = "Name of the function that uses CLASSNAME")
    option_parser.add_option("--from-class", dest = "from_class",
                             type = "string",
                             help = "Name of the class that uses CLASSNAME")
    
    # handle option or argument error.
    options, args = option_parser.parse_args(args = argv)
    return option_parser, options, args

    
def main(argv = sys.argv[1:]):
    option_parser, options, args = parse_options(argv)
    if len(args) != 2:
        option_parser.error("Please input source file and class name.")

    src, class_to_extract = args
    if not os.path.exists(src):
        option_parser.error("Source file doesn't exist: %s" % src)

    # --from-function and --from-class are mutual exclusive
    if options.from_function and options.from_class:
        option_parser.error("options --from-function and"
                            " --from-class are mutually exclusive")
        
    methods = options.methods
    if methods is not None:
        methods = methods.split(',')

    _tu = get_tu(src, config_path= options.config,
                 cdb_path = options.cdb_path)
    # TODO: the following line should be changed to work on class in a namespace
    
    ns_and_cls_names = class_to_extract.split('::')
    curr_cursor = _tu.cursor
    
    for name in ns_and_cls_names:
        for cur in curr_cursor.get_children():
            if semantic.is_class_definition(cur, name) or\
                semantic.is_namespace_definition(cur, name):                
                curr_cursor = cur
                break
        else:
            print "source file %s does not contain any class named %s" % \
                (src, class_to_extract)
            sys.exit(1)
            
    if curr_cursor is None or not semantic.is_class_definition(curr_cursor):
        sys.stderr.write("source file %s does not contain any class named %s\n" % \
            (src, class_to_extract))
        sys.exit(1)


    # If user specifies to extract a class from other function's usage,
    # analyze the function
    fun_using_class = options.from_function
    if fun_using_class is not None:
        fun_cursor = get_cursor_if(_tu,
                                   partial(semantic.is_function_definition,
                                           fun_name = fun_using_class))
        methods = semantic.get_func_callee_names(
            fun_cursor, class_to_extract)

    cls_using_class = options.from_class
    if cls_using_class is not None:
        cls_cursor = get_cursor_if(_tu,
                                   partial(semantic.is_class_definition,
                                           class_name = cls_using_class))
        methods = semantic.get_class_callee_names(cls_cursor, class_to_extract)

    # print out the interface class
    class_printer = extract_interface(curr_cursor, methods)
    print class_printer.get_definition()

if __name__ == '__main__':
    main()
        
