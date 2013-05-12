from reshaper.classprinter import ClassPrinter
from reshaper.util import get_cursors_if
from clang.cindex import CursorKind
from reshaper.ast import get_tu
import os

INPUT_DIR = os.path.join(os.path.dirname(__file__), 'test_data')


def test_get_definition():
    expected_class = \
"""class A
{
public:
    virtual ~A {}
};"""

    class_A = ClassPrinter('A')
    assert(expected_class == class_A.get_definition())

    SOURCE = os.path.join(INPUT_DIR, 'class.h')
    _tu = get_tu(SOURCE)
    methods = get_cursors_if(_tu,
                             (lambda c: c.kind == CursorKind.CXX_METHOD and
                              c.spelling == 'foo'))
    assert(len(methods) == 1)
    class_A.set_methods(methods)

    expected_class = \
"""class A
{
public:
    virtual ~A {}
    virtual void foo() = 0;
};"""
    assert(expected_class == class_A.get_definition())
    