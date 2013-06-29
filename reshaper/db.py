from sqlalchemy import create_engine, Column, ForeignKey
from sqlalchemy import Integer, String, Boolean
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
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

    element_count = Column(Integer, nullable = True)
    spelling = Column(String, nullable = False)
    
    is_const_qualified = Column(Boolean, nullable = False)
    is_volatile_qualified = Column(Boolean, nullable = False)
    is_restrict_qualified = Column(Boolean, nullable = False)
    is_function_variadic = Column(Boolean, nullable = False)
    is_pod = Column(Boolean, nullable = False)

    pointee_id = Column(Integer, ForeignKey(id))
    pointer = relationship("Type",

                        # cascade deletions
                        cascade="all",
                        
                        # One-to-One
                        uselist=False,

                        # many to one + adjacency list - remote_side
                        # is required to reference the 'remote'
                        # column in the join condition.
                        backref=backref("pointee", remote_side=id))

    kind_id = Column(Integer, ForeignKey("type_kind.id"))
    kind = relationship('TypeKind',
                        backref = backref('types', order_by = id))


    def __init__(self, cursor_type):
        if cursor_type.kind == clang.cindex.TypeKind.CONSTANTARRAY or \
           cursor_type.kind == clang.cindex.TypeKind.VECTOR:
            self.element_count = cursor_type.element_count
        self.spelling = cursor_type.spelling
        self.is_const_qualified = cursor_type.is_const_qualified()
        self.is_volatile_qualified = cursor_type.is_volatile_qualified()
        self.is_restrict_qualified = cursor_type.is_restrict_qualified()
        if cursor_type.kind == clang.cindex.TypeKind.FUNCTIONPROTO:
            self.is_function_variadic = cursor_type.is_function_variadic()
        else:
            self.is_function_variadic = False
        self.is_pod = cursor_type.is_pod()

    @staticmethod
    def from_clang_type(cursor_type):
        try:
            _type = _session.query(Type).join(TypeKind).\
                filter(TypeKind.name == cursor_type.kind.name).\
                filter(Type.spelling == cursor_type.spelling).\
                filter(Type.is_const_qualified ==
                       cursor_type.is_const_qualified()).one()
        except MultipleResultsFound, e:
            print e
            raise
        except NoResultFound: # The type has not been stored in DB.
            _type = Type(cursor_type)
            _type.kind = TypeKind.from_clang_type_kind(cursor_type.kind)

        # take care for the BLOCKPOINTER
        if cursor_type.kind == clang.cindex.TypeKind.POINTER:
            _type.pointee = Type.from_clang_type(cursor_type.get_pointee())
            
        return _type
        

class TypeKind(_Base):

    __tablename__ = "type_kind"
    
    id = Column(Integer, primary_key = True)
    
    name = Column(String, nullable = False)
    spelling = Column(String, nullable = False)

    def __init__(self, type_kind):
        self.name = type_kind.name
        self.spelling = type_kind.spelling

    @staticmethod
    def from_clang_type_kind(type_kind):
        """ Get the DB TypeKind from clang's TypeKind
        
        Arguments:
        - `type_kind`:
        """

        query = _session.query(TypeKind).filter(TypeKind.name == type_kind.name)
        return query.first()
        


_Base.metadata.create_all(_engine) 

_Session = sessionmaker(bind=_engine)
_session = _Session()


def build_db_tree(cursor):

    def build_db_cursor(cursor, parent, left):
        db_cursor = Cursor(cursor)
        db_cursor.parent = parent
        db_cursor.left = left
        db_cursor.kind = CursorKind.from_clang_cursor_kind(cursor.kind)
        if cursor.type is not None and \
           cursor.type.kind != clang.cindex.TypeKind.INVALID:
            db_cursor.type = Type.from_clang_type(cursor.type)

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

def build_db_type_kind():
    all_kinds = [clang.cindex.TypeKind.from_id(_i) for _i in xrange(30)]
    all_kinds += [clang.cindex.TypeKind.from_id(_i)
                  for _i in xrange(100, 114)]

    _session.add_all([TypeKind(kind) for kind in all_kinds])
    _session.commit()

