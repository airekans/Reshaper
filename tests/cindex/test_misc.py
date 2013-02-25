import gc
import sys

from clang.cindex import CursorKind
from clang.cindex import TranslationUnit
from clang.cindex import TypeKind
from .util import get_cursor
from .util import get_cursors
from .util import get_tu


def test_underlying_type_of_multiple_typedef():
    tu = get_tu('typedef int foo; typedef foo bar;')
    typedef_bar = get_cursor(tu, 'bar')
    typedef_foo = get_cursor(tu, 'foo')
    assert typedef_bar is not None

    assert typedef_bar.kind.is_declaration()
    underlying_foo = typedef_bar.underlying_typedef_type
    assert underlying_foo.kind == TypeKind.TYPEDEF
    assert underlying_foo.get_declaration().spelling == "foo"

    assert typedef_foo.kind.is_declaration()
    underlying_int = typedef_foo.underlying_typedef_type
    assert underlying_int.kind == TypeKind.INT

    assert underlying_foo.get_canonical().kind == TypeKind.INT
    
    
    
    
    



