'test_find_reference.py -- unittest for find_reference.py'

from clang.cindex import *
from util import get_tu
from find_reference_util import getCursorForLocation
from find_reference_util import getCursorsWithParent
import find_reference as fr

globalAndNamespaceTest = """\
void TargetFunc()
{
}

namespace Test{
   void TargetFunc()
   {
   }
}
void CallMe()
{
    TargetFunc();
    Test::TargetFunc();
}

"""

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



def test_getDeclarationCursorUSR_global_namespace():

    tu = get_tu(globalAndNamespaceTest, 'cpp')
    assert(isinstance(tu, TranslationUnit))
    spelling = "TargetFunc"

    declaCursor = getCursorForLocation(tu, spelling, 1, None)
    assert(isinstance(declaCursor, Cursor))
    declaUSR = declaCursor.get_usr()
    assert(declaUSR)

    refOne = getCursorForLocation(tu, spelling, 12, None)
    assert(isinstance(refOne, Cursor))
    refOneUSR = fr.getDeclarationCursorUSR(refOne)
    assert(refOneUSR)
    assert(declaUSR == refOneUSR)

    nameRef = getCursorForLocation(tu, spelling, 13, None)
    assert(isinstance(nameRef, Cursor))
    nameRefUSR = fr.getDeclarationCursorUSR(nameRef)
    assert(nameRefUSR)
    assert(declaUSR != nameRefUSR)
 
    nameDecl = getCursorForLocation(tu, spelling, 6, None)
    assert(isinstance(nameDecl, Cursor))
    nameDeclUSR = fr.getDeclarationCursorUSR(nameDecl)
    assert(nameDeclUSR)
    assert(declaUSR != nameDeclUSR)

    assert(nameDeclUSR == nameRefUSR)

def test_getDeclarationCursorUSR_mem():

    tu = get_tu(memTest, 'cpp')
    assert(isinstance(tu, TranslationUnit))
    spelling = "TargetFunc"

    tarCur = getCursorForLocation(tu, spelling, 4, None)
    assert(isinstance(tarCur, Cursor))
    tarUSR = tarCur.get_usr()
    assert(tarUSR)

    nsCur = getCursorForLocation(tu, spelling, 11, None)
    assert(isinstance(nsCur, Cursor))
    nsUSR = nsCur.get_usr()
    assert(nsUSR)

    memRefCur = getCursorForLocation(tu, spelling, 19, None)
    assert(isinstance(memRefCur, Cursor))
    memRefUSR = fr.getDeclarationCursorUSR(memRefCur)
    assert(memRefUSR)

    namRefCur = getCursorForLocation(tu, spelling, 21, None)
    assert(isinstance(namRefCur, Cursor))
    namRefUSR = fr.getDeclarationCursorUSR(namRefCur)
    assert(namRefUSR)

    assert(tarUSR == memRefUSR)
    assert(tarUSR != nsUSR)
    assert(nsUSR == namRefUSR)

def test_getDeclarationCursorUSR_template():
    #FIXME:template class and template function; its declaration USR is different from USR after template instantiations, such as call, template speciallization 
    pass

def test_removeFakeByUSR():
    tu = get_tu(memTest, 'cpp')
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
    test_getDeclarationCursorUSR_global_namespace()
    test_getDeclarationCursorUSR_mem()
    test_getDeclarationCursorUSR_template()
    test_removeFakeByUSR()
