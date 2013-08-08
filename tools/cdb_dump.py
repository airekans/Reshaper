#! /usr/bin/env python

try:
    import json
except ImportError:
    import simplejson as json
    
import sys
import os
import re
from optparse import OptionParser


def join_if_relative_path(prefix_path, path):
    if path[0] != '/':
        return os.path.join(prefix_path, path)
    else:
        return path

def transform_compile_command(cmd, work_dir):
    i, cmd_len = 0, len(cmd)
    while i < cmd_len:
        arg = cmd[i]
        if arg.startswith('-I'):
            if arg == '-I': # in the form of "-I path"
                cmd[i + 1] = join_if_relative_path(work_dir, cmd[i + 1])
                i += 1
            else:
                include_path = join_if_relative_path(work_dir, arg[2:])
                arg = '-I' + include_path
                cmd[i] = arg

        i += 1

def convert_file_to_cdb(in_fd, work_dir):
    compile_command_regex = \
        re.compile(r"^(?P<CC>gcc)(?P<infix> .*-c )(?P<file>\S+) (?P<suffix>.*)$")
    cdb = []
    for line in in_fd:
        result = compile_command_regex.match(line)
        if result is not None:
            cmd_str = ''.join(['clang++', result.group('infix'),
                           result.group('suffix')])
            
            cmd = cmd_str.split()
            transform_compile_command(cmd, work_dir)

            cdb.append({
                "directory": work_dir,
                "command": ' '.join(cmd),
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