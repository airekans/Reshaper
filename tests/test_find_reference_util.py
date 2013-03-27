from clang.cindex import *
from util import get_tu
import find_reference_util as fr_util
import find_reference as fr

'test_find_reference.py -- unittest for find_reference_util.py'

kInput = """\
void TargetFunc()
{
}
int testVariable = 0;
void CallMe()
{
    TargetFunc();
}
void Call_CallMe()
{
    int j = 0;
    int u = (1 == true ?testVariable : (testVariable+1));
    CallMe();
    TargetFunc();
}

"""

def test_getCursorsWithParent():
    tu = get_tu(kInput, 'cpp')
    assert(isinstance(tu, TranslationUnit))
    spelling = "TargetFunc"
    cursors = fr_util.getCursorsWithParent(tu, spelling)
    for cursor in cursors:
        assert(isinstance(cursor, Cursor))
        if cursor.location.line == 1:
            assert(isinstance(cursor.parent, TranslationUnit))
            hasChild = False
            children = cursor.parent.cursor.get_children()
            for ch in children:
                if ch == cursor:
                    hasChild = True
            assert(hasChild)

        else:
            assert(isinstance(cursor.parent, Cursor))
            hasChild = False
            children = cursor.parent.get_children()
            for ch in children:
                if ch == cursor:
                    hasChild = True
            assert(hasChild)

def test_getCursorForLocation():
    tu = get_tu(kInput, 'cpp')
    assert(isinstance(tu, TranslationUnit))
    spelling = "testVariable"
    cursor1 = fr_util.getCursorForLocation(tu, spelling, 1, None)
    assert(not cursor1)
    cursor2 = fr_util.getCursorForLocation(tu, spelling, 4, 10)
    assert(not cursor2)
    cursor3 = fr_util.getCursorForLocation(tu, spelling, 12, None)
    assert(isinstance(cursor3, Cursor))
    assert(cursor3.location.line == 12)
    assert(cursor3.location.column == 25)
    cursor4 = fr_util.getCursorForLocation(tu, spelling, 12, 41)
    assert(isinstance(cursor4, Cursor))
    assert(cursor4.location.line == 12)
    assert(cursor4.location.column == 41)

#should make sure that cursor already have parent attr
def test_getCallFunc():
    tu = get_tu(kInput, 'cpp')
    assert(isinstance(tu, TranslationUnit))
    spelling = "TargetFunc"
    cursors = fr_util.getCursorsWithParent(tu, spelling)
    for cur in cursors:
        assert(isinstance(cur, Cursor))
        parent = fr_util.getCallFunc(cur)
        if cur.location.line == 1:
            assert(not parent)
        elif cur.location.line == 7:
            assert(isinstance(parent, Cursor))
            assert(str("CallMe") in parent.displayname)
        elif cur.location.line == 14:
            assert(isinstance(parent, Cursor))
            assert(str("Call_CallMe") in parent.displayname)

if __name__ == "__main__":
    test_getCursorsWithParent()
    test_getCursorForLocation()
    test_getCallFunc()
