'''test_transform: unittest for transform.py
'''

from reshaper.util import get_cursor_if, get_cursors_if, get_cursor_with_location
from reshaper.ast import get_tu
from clang.cindex import CursorKind
import reshaper.semantic as sem
import reshaper.encapsulator as encap
import os


_INPUT_FILE = os.path.join(os.path.dirname(__file__), 'test_data', 'transform', 'test_transform.cpp')
_INPUT_PATH = os.path.join(os.path.dirname(__file__), 'test_data', 'transform')
_HEADER_FILE = os.path.join(os.path.dirname(__file__), 'test_data', 'transform', 'test_transform.h')
_TU = get_tu(_INPUT_FILE)


def test_find_public_fields():
    cls_a = get_cursor_if(_TU, lambda cur: sem.is_class(cur) \
            and sem.is_class_name_matched(cur, 'A'))
    fields_a = encap.find_public_fields(cls_a)
    assert([cur.displayname for cur in fields_a] == ['m_i2', 'm_i4'])
    
    cls_b = get_cursor_if(_TU, lambda cur: sem.is_class(cur) \
            and sem.is_class_name_matched(cur, 'B'))
    fields_b = encap.find_public_fields(cls_b)
    assert([cur.displayname for cur in fields_b] == ['m_i', 'm_i2'])
    
    cls_c = get_cursor_if(_TU, lambda cur: sem.is_class(cur) \
            and sem.is_class_name_matched(cur, 'C'))
    fields_c = encap.find_public_fields(cls_c)
    assert(fields_c == [])
        
def test_get_prvt_fld_insert_location():
    cls_b = get_cursor_if(_TU, lambda cur: sem.is_class(cur) \
            and sem.is_class_name_matched(cur, 'B'))
    prvt_b = encap.get_prvt_fld_insert_location(cls_b)
    assert(prvt_b.location.line == 14)
    
    cls_c = get_cursor_if(_TU, lambda cur: sem.is_class(cur) \
            and sem.is_class_name_matched(cur, 'C'))
    prvt_c = encap.get_prvt_fld_insert_location(cls_c)
    assert(prvt_c.location.line == 19)

def test_find_reference_to_field():
    tu = get_tu(_HEADER_FILE)
    cls_a = get_cursor_if(tu, lambda cur: sem.is_class(cur) \
            and sem.is_class_name_matched(cur, 'A'))
    fields_a = encap.find_public_fields(cls_a)[0]
    
    refs = encap.find_reference_to_field(fields_a, _INPUT_PATH)
    assert(len(refs) == 4)

def test_get_binary_operator_opt():
    curs = get_cursors_if(_TU, lambda cur: cur.kind == CursorKind.BINARY_OPERATOR)
    assert [encap.get_binary_operator_opt(cur) for cur in curs] == ['=', '+']
    
def test_is_l_value_binary_opt():
    cls_a = get_cursor_if(_TU, lambda cur: sem.is_class(cur) \
            and sem.is_class_name_matched(cur, 'A'))
    fields_a = encap.find_public_fields(cls_a)[0]
    refs = encap.find_reference_to_field(fields_a, _INPUT_PATH)
    
    result = [encap.is_l_value(cur, _TU) for cur in refs]
    assert result ==[True, False, False, False]

def test_is_l_value_func_call():
    cls_d = get_cursor_if(_TU, lambda cur: sem.is_class(cur) \
            and sem.is_class_name_matched(cur, 'D'))
    fields_d = encap.find_public_fields(cls_d)[0]
    refs = encap.find_reference_to_field(fields_d, _INPUT_PATH)
    
    result = [encap.is_l_value(cur, _TU) for cur in refs]
    
    assert result == [True, False, False]
    
def test_add_fields():
    cls_d = get_cursor_if(_TU, lambda cur: sem.is_class(cur) \
            and sem.is_class_name_matched(cur, 'D'))
    fields_d = encap.find_public_fields(cls_d)[0]   
    refs = encap.find_reference_to_field(fields_d, _INPUT_PATH)
    
    encap.add_fields(refs, _TU)
    assert [cur.use_set_method for cur in refs] == [True, False, None]
    assert [cur.has_set_method for cur in refs] == [None, None, True]
    assert [cur.suffix for cur in refs] == ['C'] * 3
    assert [cur.end_offset - cur.start_offset for cur in refs] == [9, 5, 5]




