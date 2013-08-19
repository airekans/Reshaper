'''test_find_reference_util.py -- unittest for
find_reference_util.py
'''

from nose.tools import eq_
from reshaper.util import get_cursor_with_location
from reshaper.semantic import get_cursors_add_parent
from reshaper.find_reference_util import filter_cursors_by_usr
from reshaper.find_reference_util import get_cursors_with_name
from .util import get_tu_from_text

from os import remove

TEST_INPUT = """\
class TestClass
{
public:
    void TargetFunc()
    {
    }
};

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

def test_filter_cursurs_by_usr():
    '''test function filter_cursors_by_usr
    '''
    _tu = get_tu_from_text(TEST_INPUT)
    spelling = "TargetFunc"
    target_cursor = get_cursor_with_location(_tu, spelling, 4)
    target_usr = target_cursor.get_usr()

    candidate_curs = get_cursors_add_parent(_tu, spelling)

    eq_(len(candidate_curs), 7)
    final_curs = filter_cursors_by_usr(candidate_curs, target_usr)
    eq_(len(final_curs), 2)
    eq_(final_curs[0].location.line, 4)
    eq_(final_curs[1].location.line, 19)

def test_get_cursors_with_name():
    '''test function get_cursors_with_name
    '''
    file_name = "/tmp/test_get_cursors_with_name"
    ftmp = open(file_name, 'w')
    ftmp.write(TEST_INPUT)
    ftmp.close()
    
    name = "TargetFunc"
    ref = []
    get_cursors_with_name(file_name, name, ref)
    remove(file_name)
    eq_(len(ref), 7)
    
    ref = []
    res = get_cursors_with_name(file_name, name, ref)
    eq_(res, None)
    eq_(ref, [])

    