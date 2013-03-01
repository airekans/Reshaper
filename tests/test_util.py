from util import get_cursors_if, walk_ast
from clang.cindex import TranslationUnit
from clang.cindex import CursorKind
import os
from functools import partial

INPUT_DIR = os.path.join(os.path.dirname(__file__), 'test_data')

def test_get_cursors_if():
    SOURCE = os.path.join(INPUT_DIR, 'class.cpp')
    tu = TranslationUnit.from_source(SOURCE, ['-std=c++11'])
    assert(tu is not None)

    cursors = get_cursors_if(tu.cursor, lambda c: c.spelling == 'A')
    assert(len(cursors) == 2) # the class itself and the constructor
    for cursor in cursors:
        assert(cursor.spelling == 'A')

    assert([cursor.kind for cursor in cursors] ==
           [CursorKind.CLASS_DECL, CursorKind.CONSTRUCTOR])

    # with other conditions
    cursors = get_cursors_if(tu.cursor, lambda c: c.kind == CursorKind.CLASS_DECL)
    assert(len(cursors) == 1) # the class itself
    assert(cursors[0].kind == CursorKind.CLASS_DECL)
    assert(cursors[0].spelling == 'A')

def test_walk_ast():
    SOURCE = os.path.join(INPUT_DIR, 'class.cpp')
    tu = TranslationUnit.from_source(SOURCE, ['-std=c++11'])

    def ns(): pass
    ns.node_count = 0
    def count_level_node(_, level, expected_level = 0):
        if level == expected_level:
            ns.node_count += 1

    walk_ast(tu, count_level_node)
    assert(ns.node_count == 1)

    ns.node_count = 0
    walk_ast(tu, partial(count_level_node, expected_level = 1))
    assert(ns.node_count == 5)

    ns.node_count = 0
    walk_ast(tu, partial(count_level_node, expected_level = 2))
    assert(ns.node_count == 15)
    
    
