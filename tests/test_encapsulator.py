'''test_transform: unittest for transform.py
'''

from reshaper.util import get_cursor_if, get_cursors_if, get_cursor_with_location
from reshaper.ast import get_tu
from clang.cindex import CursorKind
from tests.util import redirect_stderr
import reshaper.semantic as sem
import reshaper.encapsulator as encap
import os


_INPUT_FILE = os.path.join(os.path.dirname(__file__), 'test_data', 'encapsulate', 'test_encap.cpp')
_INPUT_PATH = os.path.join(os.path.dirname(__file__), 'test_data', 'encapsulate')
_HEADER_FILE = os.path.join(os.path.dirname(__file__), 'test_data', 'encapsulate', 'test_encap.h')
_TU = get_tu(_INPUT_FILE)

def test_find_public_fields():
    '''test find_public_fields() 
    '''
    cls_a = get_cursor_if(_TU, lambda cur: sem.is_class(cur) \
            and sem.is_class_name_matched(cur, 'A'))
    fields_a = encap.find_public_fields(cls_a)
    assert([cur.displayname for cur in fields_a] == ['m_i2', 'm_i4'])
    
    fields_a = encap.find_public_fields(cls_a, ['m_i1', 'm_i2', 'm_i3', 'm_i5'])
    assert([cur.displayname for cur in fields_a] == ['m_i2'])
    
    cls_b = get_cursor_if(_TU, lambda cur: sem.is_class(cur) \
            and sem.is_class_name_matched(cur, 'B'))
    fields_b = encap.find_public_fields(cls_b)
    assert([cur.displayname for cur in fields_b] == ['m_i', 'm_i2'])
    
    cls_c = get_cursor_if(_TU, lambda cur: sem.is_class(cur) \
            and sem.is_class_name_matched(cur, 'C'))
    fields_c = encap.find_public_fields(cls_c)
    assert(fields_c == [])

def test_get_prvt_fld_insert_location():
    '''test get_prvt_fld_insert_location()
    '''
    cls_b = get_cursor_if(_TU, lambda cur: sem.is_class(cur) \
            and sem.is_class_name_matched(cur, 'B'))
    prvt_b = encap.get_prvt_fld_insert_location(cls_b)
    assert(prvt_b.location.line == 14)
    
    cls_c = get_cursor_if(_TU, lambda cur: sem.is_class(cur) \
            and sem.is_class_name_matched(cur, 'C'))
    prvt_c = encap.get_prvt_fld_insert_location(cls_c)
    assert(prvt_c.location.line == 19)

def test_find_reference_to_field():
    '''test find_reference_to_field()
    '''
    tu = get_tu(_HEADER_FILE)
    cls = get_cursor_if(tu, lambda cur: sem.is_class(cur) \
            and sem.is_class_name_matched(cur, 'A'))
    field = encap.find_public_fields(cls)[0]
    
    refs = encap.find_reference_to_field(field, _INPUT_PATH)
    assert(len(refs) == 4)

def test_get_binary_operator_opt():
    '''test get_binary_operator
    '''
    curs = get_cursors_if(_TU, lambda cur: cur.kind == CursorKind.BINARY_OPERATOR)
    assert [encap.get_binary_operator_opt(cur) for cur in curs] == ['=', '+', '=']
    
def test_is_l_value_binary_opt():
    '''test is_l_value() on binary operator '='
    '''
    cls = get_cursor_if(_TU, lambda cur: sem.is_class(cur) \
            and sem.is_class_name_matched(cur, 'A'))
    field = encap.find_public_fields(cls)[0]
    refs = encap.find_reference_to_field(field, _INPUT_PATH)
    
    result = [encap.is_l_value(cur, _TU) for cur in refs]
    assert result ==[True, False, False, False]

def test_is_l_value_func_call():
    '''test is_l_value() on function call 'operator='
    '''
    cls = get_cursor_if(_TU, lambda cur: sem.is_class(cur) \
            and sem.is_class_name_matched(cur, 'D'))
    field = encap.find_public_fields(cls)[0]
    refs = encap.find_reference_to_field(field, _INPUT_PATH)
    
    result = [encap.is_l_value(cur, _TU) for cur in refs]
    
    assert result == [True, False, False]
    
def test_add_fields():
    '''test add_fields()
    '''
    cls = get_cursor_if(_TU, lambda cur: sem.is_class(cur) \
            and sem.is_class_name_matched(cur, 'D'))
    field = encap.find_public_fields(cls)[0]   
    refs = encap.find_reference_to_field(field, _INPUT_PATH)
    
    encap.add_fields(refs, _TU)
    assert [cur.use_set_method for cur in refs] == [True, False, None]
    assert [cur.has_set_method for cur in refs] == [None, None, True]
    assert [cur.suffix for cur in refs] == ['C'] * 3
    assert [cur.end_offset - cur.start_offset for cur in refs] == [9, 5, 5]

def test_filter_reference_in_cls_method():
    cls = get_cursor_if(_TU, lambda cur: sem.is_class(cur) \
            and sem.is_class_name_matched(cur, 'E'))
    fields = encap.find_public_fields(cls)
    
    ref_cur = []
    for field in fields:
        ref_cur += encap.find_reference_to_field(field, _INPUT_PATH)
    assert len(ref_cur) == 5    
        
    encap.filter_reference_in_cls_method(ref_cur, cls)
    assert len(ref_cur) == 3

def test_filter_fields_has_get_set():
    cls = get_cursor_if(_TU, lambda cur: sem.is_class(cur) \
            and sem.is_class_name_matched(cur, 'E'))
    fields = encap.find_public_fields(cls)
    assert len(fields) == 3

    encap.filter_fields_has_get_set(fields, cls)
    assert len(fields) == 2