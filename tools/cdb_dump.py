#! /usr/bin/env python

import json
import sys
import os
import re
from optparse import OptionParser


def convert_file_to_cdb(in_fd, work_dir):
    compile_command_regex = \
        re.compile(r"^(?P<CC>gcc)(?P<infix> .*-c )(?P<file>\S+) (?P<suffix>.*)$")
    cdb = []
    for line in in_fd:
        result = compile_command_regex.match(line)
        if result is not None:
            cdb.append({
                "directory": work_dir,
                "command": ''.join(['clang++', result.group('infix'),
                                    result.group('suffix')]),
                "file": result.group("file")
            })

    return cdb

def main():
    """ main flow of the program
    """
    option_parser = OptionParser(usage = "%prog [options] FILE")
    option_parser.add_option("-o", dest = "out_file",
                             type = "string",
                             default = "compile_commands.json",
                             help = "file name of the cdb file."
                             " If not given, use compile_commands.json.")
    option_parser.add_option("-d", "--directory", dest = "work_dir",
                             type = "string",
                             default = os.getcwd(),
                             help = "Working directory of the compile commands."
                             " If not given, use current working directory.")
    options, args = option_parser.parse_args()
    
    if len(args) < 1:
        option_parser.error("Please give input file")
    
    in_file = args[0]
    out_file = options.out_file
    
    in_fd = open(in_file)
    cdb = convert_file_to_cdb(in_fd, options.work_dir)
    out_fd = open(out_file, 'w')
    json.dump(cdb, out_fd, indent=2)


if __name__ == '__main__':
    main()