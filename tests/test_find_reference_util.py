from clang.cindex import *
import reshaper.find_reference_util as fr_util

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

decSemParInput = """\
class TestClass
{
public:
    void classFunc()
    {
    }
};

namespace TestName
{
    void nameFunc()
    {
    }
}

namespace
{
    void annoyNameFunc()
    {
    }
}

void GlobalFunc()
{
}

void CallFunc()
{
   TestClass tc;
   tc.classFunc();
   TestName::nameFunc();
   ::annoyNameFunc();
   GlobalFunc();
}
"""

#copy it from util.py, just for test
def get_tu_from_text(source, lang='cpp'):
    name = 't.cpp'
    args = []
    args.append('-std=c++11')

    return TranslationUnit.from_source(name, args, unsaved_files=[(name,
                                       source)])


def test_getCursorsWithParent():
    tu = get_tu_from_text(kInput, 'cpp')
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
    tu = get_tu_from_text(kInput, 'cpp')
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
    tu = get_tu_from_text(kInput, 'cpp')
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

def get_decla_tu():
    tu = get_tu_from_text(decSemParInput , 'cpp')
    assert(isinstance(tu, TranslationUnit))
    return tu

def test_getDeclareationCursor_getDeclSemanticParent_class():
    tu = get_decla_tu()
    spelling = "classFunc"
    curClass = fr_util.getCursorForLocation(tu, spelling, 30, None)
    assert(isinstance(curClass, Cursor))
    decCur = fr_util.getDeclarationCursor(curClass)
    assert(decCur.location.line == 4)
    assert(decCur.kind == CursorKind.CXX_METHOD)
    semaParent = fr_util.getDeclSemanticParent(curClass)
    assert(semaParent == decCur.semantic_parent)
    assert(semaParent.kind == CursorKind.CLASS_DECL)

def test_getDeclareationCursor_getDeclSemanticParent_namespace():
    tu = get_decla_tu()
    spelling = "nameFunc"
    cur = fr_util.getCursorForLocation(tu, spelling, 31, None)
    assert(isinstance(cur, Cursor))
    decCur = fr_util.getDeclarationCursor(cur)
    assert(decCur.location.line == 11)
    assert(decCur.kind == CursorKind.FUNCTION_DECL)
    semaParent = fr_util.getDeclSemanticParent(cur)
    assert(semaParent == decCur.semantic_parent)
    assert(semaParent.kind == CursorKind.NAMESPACE)

def test_getDeclareationCursor_getDeclSemanticParent_anamespace():
    tu = get_decla_tu()
    spelling = "annoyNameFunc"
    cur = fr_util.getCursorForLocation(tu, spelling, 32, None)
    assert(isinstance(cur, Cursor))
    decCur = fr_util.getDeclarationCursor(cur)
    assert(decCur.location.line == 18)
    assert(decCur.kind == CursorKind.FUNCTION_DECL)
    semaParent = fr_util.getDeclSemanticParent(cur)
    assert(semaParent == decCur.semantic_parent)
    assert(semaParent.kind == CursorKind.NAMESPACE)

def test_getDeclareationCursor_getDeclSemanticParent_global():
    tu = get_decla_tu()
    spelling = "GlobalFunc"
    cur = fr_util.getCursorForLocation(tu, spelling, 33, None)
    assert(isinstance(cur, Cursor))
    decCur = fr_util.getDeclarationCursor(cur)
    assert(decCur.location.line == 23)
    assert(decCur.kind == CursorKind.FUNCTION_DECL)
    semaParent = fr_util.getDeclSemanticParent(cur)
    assert(semaParent == decCur.semantic_parent)
    assert(semaParent.kind == CursorKind.TRANSLATION_UNIT)



if __name__ == "__main__":
    test_getCursorsWithParent()
    test_getCursorForLocation()
    test_getCallFunc()
    test_getDeclareationCursor_getDeclSemanticParent_class()
    test_getDeclareationCursor_getDeclSemanticParent_namespace()
    test_getDeclareationCursor_getDeclSemanticParent_anamespace()
    test_getDeclareationCursor_getDeclSemanticParent_global()
