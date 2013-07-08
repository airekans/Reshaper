from sqlalchemy import create_engine, Column, ForeignKey
from sqlalchemy import Integer, String, Boolean
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm import composite
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.schema import Table
import weakref
import clang.cindex

_engine = create_engine('sqlite:///test.db', echo=False)
_Base = declarative_base()


class FileInclusion(_Base):

    __tablename__ = 'file_inclusion'
    
    including_id = Column('including_id', Integer,
                          ForeignKey('file.id'),
                          primary_key=True)
    included_id = Column('included_id', Integer,
                         ForeignKey('file.id'),
                         primary_key=True)



class File(_Base):
    """ DB representation for c++ files.
    """

    __tablename__ = 'file'

    id = Column(Integer, primary_key = True)
    
    name = Column(String, nullable = True)
    time = Column(Integer, nullable = False)

    include_table = Table('include', _Base.metadata,
                              Column('including_id', Integer,
                                     ForeignKey('file.id')),
                              Column('included_id', Integer,
                                     ForeignKey('file.id')))
    includes = relationship("File",
                            secondary = include_table,
                            backref = "included_by",
                            primaryjoin = id == include_table.c.including_id,
                            secondaryjoin = id == include_table.c.included_id)
    

    
    def __init__(self, clang_file):
        """
        
        Arguments:
        - `clang_file`:
        """
        self.name = clang_file.name
        self.time = clang_file.time
    
    @staticmethod
    def from_clang_tu(tu, name):
        clang_file = tu.get_file(name)
        try:
            _file = _session.query(File).\
                filter(File.name == clang_file.name).one()
        except MultipleResultsFound, e:
            print e
            raise
        except NoResultFound: # The type has not been stored in DB.
            _file = File(clang_file)
            _file.includes = []
            for include in tu.get_includes():
                if include.source.name == _file.name:
                    _file.includes.append(
                        File.from_clang_tu(tu, include.include.name))
        
        return _file

class SourceLocation(object):
    """ DB representation of clang SourceLocation
    """
    
    def __init__(self, line, column, offset):
        """
        
        Arguments:
        - `line`:
        - `column`:
        - `offset`:
        """
        self.line = line
        self.column = column
        self.offset = offset
        
    def __composite_values__(self):
        return self.line, self.column, self.offset

    def __eq__(self, other):
        return self.line == other.line and \
            self.column == other.column and \
            self.offset == other.offset

    def __ne__(self, other):
        return not self.__eq__(other)


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
                        foreign_keys=[type_id],
                        backref = backref('instances', order_by = id))

    is_static_method = Column(Boolean, nullable = False)
    
    kind_id = Column(Integer, ForeignKey('cursor_kind.id'))
    kind = relationship('CursorKind', backref = backref('cursors', order_by = id))

    file_id = Column(Integer, ForeignKey('file.id'))
    file = relationship("File")

    # location
    line_start = Column(Integer, nullable = False)
    column_start = Column(Integer, nullable = False)
    offset_start = Column(Integer, nullable = False)

    line_end = Column(Integer, nullable = False)
    column_end = Column(Integer, nullable = False)
    offset_end = Column(Integer, nullable = False)

    location_start = composite(SourceLocation, line_start, column_start,
                               offset_start)
    location_end = composite(SourceLocation, line_end, column_end,
                             offset_end)

    # adjacent_list attributes
    parent_id = Column(Integer, ForeignKey(id))
    children = relationship("Cursor",

                        # cascade deletions
                        cascade="all",
                        foreign_keys=[parent_id],
                        # many to one + adjacency list - remote_side
                        # is required to reference the 'remote'
                        # column in the join condition.
                        backref=backref("parent", remote_side=id))

    # definition
    definition_id = Column(Integer, ForeignKey(id))
    declarations = relationship("Cursor",
                                # cascade deletions
                                cascade="all",
                                foreign_keys=[definition_id],
                                backref=backref("definition", remote_side=id))

    # nested set attributes
    left = Column("left", Integer, nullable=False)
    right = Column("right", Integer, nullable=True)

    
    def __init__(self, cursor):
        self.spelling = cursor.spelling
        self.displayname = cursor.displayname
        self.usr = cursor.get_usr()
        self.is_definition = cursor.is_definition()
        self.is_static_method = cursor.is_static_method()

        location_start = cursor.extent.start
        location_end = cursor.extent.end
        self.location_start = SourceLocation(location_start.line,
                                             location_start.column,
                                             location_start.offset)
        self.location_end = SourceLocation(location_end.line,
                                           location_end.column,
                                           location_end.offset)
        

    @staticmethod
    def from_clang_declaration(cursor):
        # if the cursor itself is a definition, then find out all the declaration cursors
        # that refer to it.
        # if the cursor is a declaration, then get the definition cursor

        assert cursor.is_definition()
        if cursor.get_usr() == "": # builtin definitions
            return None
        
        try:
            _cursor = _session.query(Cursor).\
                filter(Cursor.usr == cursor.get_usr()).\
                filter(Cursor.is_definition == True).one()
        except MultipleResultsFound, e:
            print "usr", cursor.get_usr()
            print ""
            print e
            raise
        except NoResultFound: # The cursor has not been stored in DB.
            _cursor = None

        return _cursor

    @staticmethod
    def from_definition(cursor):
        assert cursor.is_definition
        try:
            _cursors = _session.query(Cursor).\
                filter(Cursor.usr == cursor.usr).\
                filter(Cursor.is_definition == False).all()
        except MultipleResultsFound, e:
            print e
            raise
        except NoResultFound: # The cursor has not been stored in DB.
            _cursors = []

        for _cursor in _cursors:
            _cursor.definition = cursor

        _session.add_all(_cursors)
        
    @staticmethod
    def from_clang_cursor(cursor):
        """ Static method to create a cursor from libclang's cursor
        
        Arguments:
        - `cursor`:
        """

        try:
            _cursor = _session.query(Cursor).join(File).\
                filter(Cursor.usr == cursor.get_usr()).one()
        except MultipleResultsFound, e:
            print e
            raise
        except NoResultFound: # The cursor has not been stored in DB.
            _cursor = Cursor(cursor)

        return _cursor

        
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

    declaration_id = Column(Integer,
                            ForeignKey("cursor.id", use_alter=True,
                                       name="type_decl"))
    declaration = relationship(Cursor, foreign_keys=[declaration_id],
                               post_update=True)
    

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
    def is_valid_clang_type(cursor_type):
        return cursor_type is not None and \
            cursor_type.kind != clang.cindex.TypeKind.INVALID
        
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

    _tu = cursor.translation_unit

    def build_db_cursor(cursor, parent, left):
        db_cursor = Cursor(cursor)
        db_cursor.parent = parent
        db_cursor.left = left
        db_cursor.kind = CursorKind.from_clang_cursor_kind(cursor.kind)
        if Type.is_valid_clang_type(cursor.type):
            db_cursor.type = Type.from_clang_type(cursor.type)

        if cursor.location.file:
            db_cursor.file = File.from_clang_tu(_tu, cursor.location.file.name)

        def_cursor = cursor.get_definition()
        if def_cursor is not None:
            if cursor.is_definition():
                Cursor.from_definition(db_cursor)
            else:
                db_cursor.definition = \
                    Cursor.from_clang_declaration(def_cursor)
                
        child_left = left + 1
        for child in cursor.get_children():
            child_left = build_db_cursor(child, db_cursor, child_left) + 1

        right = child_left
        db_cursor.right = right

        _session.add(db_cursor)
        _session.commit()

        if Type.is_valid_clang_type(cursor.type) and \
                (db_cursor.type.declaration is None or
                 db_cursor.is_definition):
            db_cursor.type.declaration = db_cursor
            _session.add(db_cursor.type)
            _session.commit()

        _session.expire(db_cursor)
        
        return right

    left = 0
    if cursor.kind == clang.cindex.CursorKind.TRANSLATION_UNIT:
        for child in cursor.get_children():
            left = build_db_cursor(child, None, left) + 1
    else:
        build_db_cursor(cursor, None, left)

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

def build_db_file(tu):
    all_files = []
    for include in tu.get_includes():
        all_files.append(File.from_clang_tu(tu, include.source.name))

    _session.add_all(all_files)
    _session.commit()
    
