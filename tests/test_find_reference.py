'test_find_reference.py -- unittest for find_reference.py'

from clang.cindex import * 
from reshaper.util import get_tu
from reshaper.find_reference_util import getCursorForLocation
from reshaper.find_reference_util import getCursorsWithParent
import find_reference as fr

memTest = """\
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

#copy it from util.py, just for test
def get_tu_from_text(source, lang='cpp'):
    name = 't.cpp'
    args = []
    args.append('-std=c++11')

    return TranslationUnit.from_source(name, args, unsaved_files=[(name,
                                       source)])


def test_removeFakeByUSR():
    tu = get_tu_from_text(memTest)
    assert(isinstance(tu, TranslationUnit))
    spelling = "TargetFunc"
    tarCur = getCursorForLocation(tu, spelling, 4, None)
    assert(isinstance(tarCur, Cursor))
    tarUSR = tarCur.get_usr()

    candiCurs = getCursorsWithParent(tu, spelling)

    assert(len(candiCurs) > 2)
    finalCurs = fr.removeFakeByUSR(candiCurs, tarUSR)
    assert(len(finalCurs) == 2)
    assert(finalCurs[0].location.line == 4)
    assert(finalCurs[1].location.line == 19)


if __name__ == "__main__":
    test_removeFakeByUSR()
