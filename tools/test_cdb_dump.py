""" UT for functions in cdb_dump """

from nose.tools import eq_
import StringIO
import cdb_dump


def test_convert_file_to_cdb():
    test_input = """
cd ./ui/ && export LD_LIBRARY_PATH="/usr/local/lib"
test -d /objs/src/||mkdir -p /objs/src/
gcc -x c++-header -c src/precompile.h -o precompile.h.gch -I./src/ -D_LINUX_ -Wall -Wno-sign-compare -Wno-unused -g -Wno-deprecated -Wno-reorder -Winvalid-pch
    """
    
    in_fd = StringIO.StringIO(test_input)
    work_dir = "/path/to/src"
    expected_cdb = [{
        "directory": work_dir,
        "command": "clang++ -x c++-header -c -o precompile.h.gch"
            " -I./src/ -D_LINUX_ -Wall -Wno-sign-compare -Wno-unused -g"
            " -Wno-deprecated -Wno-reorder -Winvalid-pch",
        "file": "src/precompile.h"
    }]
    cdb = cdb_dump.convert_file_to_cdb(in_fd, work_dir)
    eq_(expected_cdb, cdb)
