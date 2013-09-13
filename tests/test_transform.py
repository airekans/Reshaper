'''test_transform: unittest for transform.py
'''

from reshaper.util import get_cursor_if, get_cursors_if
from reshaper.ast import get_tu
from clang.cindex import CursorKind
import reshaper.semantic as sem
import reshaper.transform as trs
import os


_INPUT_FILE = os.path.join(os.path.dirname(__file__), 'test_data', 'transform', 'test_transform.cpp')
_INPUT_PATH = os.path.join(os.path.dirname(__file__), 'test_data', 'transform')
_HEADER_FILE = os.path.join(os.path.dirname(__file__), 'test_data', 'transform', 'test_transform.h')
_TU = get_tu(_INPUT_FILE)


def test_find_public_fields():
    cls_a = get_cursor_if(_TU, lambda cur: sem.is_class(cur) \
            and sem.is_class_name_matched(cur, 'A'))
    fields_a = trs.find_public_fields(cls_a)
    assert([cur.displayname for cur in fields_a] == ['m_i2', 'm_i4'])
    
    cls_b = get_cursor_if(_TU, lambda cur: sem.is_class(cur) \
            and sem.is_class_name_matched(cur, 'B'))
    fields_b = trs.find_public_fields(cls_b)
    assert([cur.displayname for cur in fields_b] == ['m_i', 'm_i2'])
    
    cls_c = get_cursor_if(_TU, lambda cur: sem.is_class(cur) \
            and sem.is_class_name_matched(cur, 'C'))
    fields_c = trs.find_public_fields(cls_c)
    assert(fields_c == [])
        
def test_get_prvt_fld_insert_location():
    cls_b = get_cursor_if(_TU, lambda cur: sem.is_class(cur) \
            and sem.is_class_name_matched(cur, 'B'))
    prvt_b = trs.get_prvt_fld_insert_location(cls_b)
    assert(prvt_b.location.line == 14)
    
    cls_c = get_cursor_if(_TU, lambda cur: sem.is_class(cur) \
            and sem.is_class_name_matched(cur, 'C'))
    prvt_c = trs.get_prvt_fld_insert_location(cls_c)
    assert(prvt_c.location.line == 19)

def test_find_reference_to_field():
    tu = get_tu(_HEADER_FILE)
    cls_a = get_cursor_if(tu, lambda cur: sem.is_class(cur) \
            and sem.is_class_name_matched(cur, 'A'))
    fields_a = trs.find_public_fields(cls_a)[0]
    
    refs = trs.find_reference_to_field(fields_a, _INPUT_PATH)
    assert len(refs) == 4

def test_get_binary_operator_opt():
    curs = get_cursors_if(_TU, lambda cur: cur.kind == CursorKind.BINARY_OPERATOR)
    assert [trs.get_binary_operator_opt(cur) for cur in curs] == ['=', '+']

test_find_public_fields()
test_get_prvt_fld_insert_location()
test_find_reference_to_field()
test_get_binary_operator_opt()
print 'ok'




