from reshaper import db
from reshaper.ast import get_tu
from clang.cindex import TranslationUnit
import sys
import ipdb

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print ""

    proj_engine = db.ProjectEngine('test')

    for filename in sys.argv[1:]:
        _tu = get_tu(filename, is_from_cache_first = False)
        proj_engine.build_db_tree(_tu.cursor)

    ipdb.set_trace()
    
