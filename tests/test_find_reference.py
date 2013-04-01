'test_find_reference.py -- unittest for find_reference.py'

from clang.cindex import  TranslationUnit
from clang.cindex import  Cursor
from reshaper.find_reference_util import get_cursor_with_location
from reshaper.find_reference_util import get_cursors_add_parent
from nose.tools import eq_
import find_reference as fr

member_test = """\
class TestClass
{
public:
    void TargetFunc()
    {
    }
}

namespace TestNS
{
    void TargetFunc()
    {
    }
}

void CallFunc()
{
    TestClass *pTC = new TestClass();
    pTC->TargetFunc();

    TestNS::TargetFunc();
}
"""

def get_tu_from_text(source):
    '''copy it from util.py, 
    just for test
    '''
    name = 't.cpp'
    args = []
    args.append('-std=c++11')

    return TranslationUnit.from_source(name, args, unsaved_files=[(name,
                                       source)])


def test_remove_fake_by_usr():
    '''test function remove_fake_by_usr
    '''
    tu = get_tu_from_text(member_test)
    assert(isinstance(tu, TranslationUnit))
    spelling = "TargetFunc"
    target_cursor = get_cursor_with_location(tu, spelling, 4, None)
    assert(isinstance(target_cursor, Cursor))
    target_usr = target_cursor.get_usr()

    candidate_curs = get_cursors_add_parent(tu, spelling)

    assert(len(candidate_curs) > 2)
    final_curs = fr.filter_cursors_by_usr(candidate_curs, target_usr)
    eq_(len(final_curs), 2)
    eq_(final_curs[0].location.line, 19)
    eq_(final_curs[1].location.line, 4)

