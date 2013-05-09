import json
import sys
import re

WORK_DIR = "/home/yahuang/programming/yahuang-bc-tflex-gui-10/"

def main():
    """ main flow of the program
    """
    if len(sys.argv) < 3:
        print "Please give input file and output file"
        sys.exit(1)
    
    in_file = sys.argv[1]
    out_file = sys.argv[2]

    compile_command_regex = re.compile(r"^gcc .*-c (?P<file>\S+)")
    in_fd = open(in_file)
    cdb = []
    for line in in_fd:
        result = compile_command_regex.match(line)
        if result is not None:
            cdb.append({
                "directory": WORK_DIR,
                "command": line.strip(),
                "file": result.group("file")
            })

    print json.dumps(cdb, indent=2)

if __name__ == '__main__':
    main()