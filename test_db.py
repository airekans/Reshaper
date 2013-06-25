from reshaper import db
from reshaper.ast import get_tu
from clang.cindex import TranslationUnit
import sys
import ipdb

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print ""
    
    tu = get_tu(sys.argv[1], is_from_cache_first = False)
    db.build_db_tree(tu.cursor)

    ipdb.set_trace()

