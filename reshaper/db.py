from sqlalchemy import create_engine, Column, ForeignKey
from sqlalchemy import Integer, String, Boolean
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.collections import attribute_mapped_collection
import weakref
import clang.cindex

_engine = create_engine('sqlite:///test.db', echo=False)
_Base = declarative_base()


class Cursor(_Base):
    " Cursor DB representation  "
    
    __tablename__ = 'cursor'
    __mapper_args__ = {
        'batch': False  # allows extension to fire for each
                        # instance before going to the next.
    }

    id = Column(Integer, primary_key = True)
    spelling = Column(String, nullable = True)
    displayname = Column(String, nullable = False)
    usr = Column(String, nullable = True)
    is_definition = Column(Boolean, nullable = False)

    type_id = Column(Integer, ForeignKey('type.id'))
    type = relationship('Type',
                        backref = backref('instances', order_by = id))

    is_static_method = Column(Boolean, nullable = False)
    
    kind_id = Column(Integer, ForeignKey('cursor_kind.id'))
    kind = relationship('CursorKind', backref = backref('cursors', order_by = id))
    
    # adjacent_list attributes
    parent_id = Column(Integer, ForeignKey(id))
    children = relationship("Cursor",

                        # cascade deletions
                        cascade="all",

                        # many to one + adjacency list - remote_side
                        # is required to reference the 'remote'
                        # column in the join condition.
                        backref=backref("parent", remote_side=id))

    # nested set attributes
    left = Column("left", Integer, nullable=False)
    right = Column("right", Integer, nullable=True)


    def __init__(self, cursor):
        self.spelling = cursor.spelling
        self.displayname = cursor.displayname
        self.usr = cursor.get_usr()
        self.is_definition = cursor.is_definition()
        self.is_static_method = cursor.is_static_method()

    @classmethod
    def from_clang_cursor(cls, cursor):
        """ Static method to create a cursor from libclang's cursor
        
        Arguments:
        - `cursor`:
        """

        return cls(cursor.spelling, cursor.displayname,
                   cursor.get_usr(), cursor.is_definition())

        
class CursorKind(_Base):
    """ The DB representation for CursorKind
    """

    __tablename__ = 'cursor_kind'

    id = Column(Integer, primary_key = True)
    name = Column(String, nullable = False)

    is_declaration = Column(Boolean, nullable = False)
    is_reference = Column(Boolean, nullable = False)
    is_expression = Column(Boolean, nullable = False)
    is_statement = Column(Boolean, nullable = False)
    is_attribute = Column(Boolean, nullable = False)
    is_translation_unit = Column(Boolean, nullable = False)
    is_preprocessing = Column(Boolean, nullable = False)
    is_unexposed = Column(Boolean, nullable = False)
    
    def __init__(self, kind):
        """
        
        Arguments:
        - `kind`:
        """
        self.name = kind.name
        self.is_declaration = kind.is_declaration()
        self.is_reference = kind.is_reference()
        self.is_expression = kind.is_expression()
        self.is_statement = kind.is_statement()
        self.is_attribute = kind.is_attribute()
        self.is_translation_unit = kind.is_translation_unit()
        self.is_preprocessing = kind.is_preprocessing()
        self.is_unexposed = kind.is_unexposed()

    @staticmethod
    def from_clang_cursor_kind(kind):
        query = _session.query(CursorKind).filter(CursorKind.name == kind.name)
        return query.first()
    

class Type(_Base):
    "Type DB represention"

    __tablename__ = 'type'
    
    id = Column(Integer, primary_key = True)
    
    is_const_qualified = Column(Boolean, nullable = False)

    def __init__(self):
        pass


_Base.metadata.create_all(_engine) 

_Session = sessionmaker(bind=_engine)
_session = _Session()


def build_db_tree(cursor):

    def build_db_cursor(cursor, parent, left):
        db_cursor = Cursor(cursor)
        db_cursor.parent = parent
        db_cursor.left = left
        db_cursor.kind = CursorKind.from_clang_cursor_kind(cursor.kind)

        child_left = left
        for child in cursor.get_children():
            child_left = build_db_cursor(child, db_cursor, child_left + 1)

        right = child_left + 1
        db_cursor.right = right
        
        _session.add(db_cursor)
        _session.commit()
        _session.expire(db_cursor)
        return right

    build_db_cursor(cursor, None, 0)

def build_db_cursor_kind():
    all_kinds = clang.cindex.CursorKind.get_all_kinds()

    _session.add_all([CursorKind(kind) for kind in all_kinds])
    _session.commit()
        

