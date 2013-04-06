#===- cindex-dump.py - cindex/Python Source Dump -------------*- python -*--===#
#
#                     The LLVM Compiler Infrastructure
#
# This file is distributed under the University of Illinois Open Source
# License. See LICENSE.TXT for details.
#
#===------------------------------------------------------------------------===#

"""
A simple command line tool for dumping a source file using the Clang Index
Library.
"""

import os

def get_diag_info(diag):
    return { 'severity' : diag.severity,
             'location' : diag.location,
             'spelling' : diag.spelling,
             'ranges' : diag.ranges,
             'fixits' : diag.fixits }


def get_info(node, recurssive=True):
    
    print node.displayname
    if not recurssive:
        children = None
    else:
        children = [get_info(c, recurssive)
                    for c in node.get_children()]
    return { 
             'kind' : node.kind,
             'type' : node.type.kind,
             'name' : node.displayname,
             'location' : node.location,
             'children' : children
            }

def main():
    from clang.cindex import Index
    from pprint import pprint

    from optparse import OptionParser
    global opts

    parser = OptionParser("usage: %prog {filename} ]")
    
    parser.disable_interspersed_args()
    (opts, args) = parser.parse_args()

    if len(args) == 0:
        filepath =  os.path.join(os.path.dirname(__file__), \
                                 './test/test_data/test.h')
    else:
        filepath = args[0]
   
    index = Index.create()
    
    
    print filepath
    
    tu = index.parse(filepath, args=['-x', 'c++'])
    if not tu:
        parser.error("unable to load input")

    pprint(('diags', map(get_diag_info, tu.diagnostics)))
    pprint(('nodes', get_info(tu.cursor)))

if __name__ == '__main__':
    main()
