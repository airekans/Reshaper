from sqlalchemy import create_engine, Column, ForeignKey
from sqlalchemy import Integer, String, Boolean
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm import composite
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.schema import Table
from sqlalchemy.sql import func
import weakref
from clang.cindex import CursorKind as ckind
import clang.cindex
import os

_Base = declarative_base()


class ProjectEngine(object):
    """ Project Engine is a DB engine specific to one project
    """
    
    def __init__(self, project_name, is_in_memory = False):
        """
        
        Arguments:
        - `project_name`: the name of the project.
        """
        self._project_name = project_name
        assert len(project_name) > 0

        # create the sqlalchemy engine
        self._db_file = project_name + '.db' if not is_in_memory else ':memory:'
        is_first_time = is_in_memory or not os.path.isfile(self._db_file)

        self._engine = create_engine(
            'sqlite:///' + self._db_file, echo=False)
        _Base.metadata.create_all(self._engine)
        _Session = sessionmaker(bind=self._engine)
        self._session = _Session()

        if is_first_time:
            print "Initialize the DB."
            self.build_db_cursor_kind()
            self.build_db_type_kind()


    def get_session(self):
        return self._session

    def build_db_cursor_kind(self):
        all_kinds = clang.cindex.CursorKind.get_all_kinds()

        self._session.add_all([CursorKind(kind) for kind in all_kinds])
        self._session.commit()

    def build_db_type_kind(self):
        all_kinds = [clang.cindex.TypeKind.from_id(_i) for _i in xrange(30)]
        all_kinds += [clang.cindex.TypeKind.from_id(_i)
                      for _i in xrange(100, 114)]

        self._session.add_all([TypeKind(kind) for kind in all_kinds])
        self._session.commit()

    def build_db_file(self, tu):
        for include in tu.get_includes():
            self._session.add(
                File.from_clang_tu(tu, include.source.name, self))

        self._session.commit()

    def build_db_tree(self, cursor):
        _tu = cursor.translation_unit
        pending_files = File.get_pending_filenames(_tu, self)
        self.build_db_file(_tu)

        def build_db_cursor(cursor, parent, left):
            if cursor.kind in [clang.cindex.CursorKind.USING_DIRECTIVE,
                               clang.cindex.CursorKind.USING_DECLARATION]:
                print "skip using directive"
                return left
            elif cursor.location.file is None:
                print "skip builtin element"
                return left
            
            db_cursor = Cursor.from_clang_cursor(cursor, self)
            db_cursor.parent = parent
            print "cursor_id", id(db_cursor), "parent_id", id(parent)
            db_cursor.left = left
            if Type.is_valid_clang_type(cursor.type):
                db_cursor.type = Type.from_clang_type(cursor.type, self)
                if db_cursor.type.declaration is None or \
                   (db_cursor.is_definition and
                    not db_cursor.type.declaration.is_definition):
                    db_cursor.type.declaration = db_cursor
                    self._session.add(db_cursor.type)

            def_cursor = cursor.get_definition()
            if def_cursor is not None:
                if cursor.is_definition():
                    Cursor.from_definition(db_cursor, self)
                else:
                    db_cursor.definition = \
                        Cursor.from_clang_declaration(def_cursor, self)

            lexical_parent = cursor.lexical_parent
            if lexical_parent is not None and \
               lexical_parent.kind != clang.cindex.CursorKind.TRANSLATION_UNIT:
                db_cursor.lexical_parent = \
                    Cursor.from_clang_cursor(lexical_parent, self)

            semantic_parent = cursor.semantic_parent
            if semantic_parent is not None and \
               semantic_parent.kind != clang.cindex.CursorKind.TRANSLATION_UNIT:
                db_cursor.semantic_parent = \
                    Cursor.from_clang_cursor(semantic_parent, self)

            refer_cursor = cursor.referenced
            if refer_cursor is not None and \
               refer_cursor.location.file is not None and \
               refer_cursor.location.file.name != cursor.location.file.name and \
               refer_cursor.location.offset != cursor.location.offset and \
               refer_cursor.kind != clang.cindex.CursorKind.TRANSLATION_UNIT:
                db_cursor.referenced = \
                    Cursor.from_clang_referenced(refer_cursor, self)

            self._session.add(db_cursor)
            # _session.commit()

            child_left = left + 1
            for child in cursor.get_children():
                child_left = build_db_cursor(child, db_cursor, child_left) + 1

            right = child_left
            db_cursor.right = right

            self._session.add(db_cursor)
            self._session.commit()
            self._session.expire(db_cursor)

            return right

        left = Cursor.get_max_nested_set_index(self)
        if left > 0:
            left += 20
        if cursor.kind == clang.cindex.CursorKind.TRANSLATION_UNIT:
            for child in cursor.get_children():
                if child.location.file and \
                        child.location.file.name in pending_files:
                    left = build_db_cursor(child, None, left) + 1
        else:
            build_db_cursor(cursor, None, left)

    
def _print_error_cursor(cursor):
    """ print the information about cursor when error occur.
    
    Arguments:
    - `cursor`:
    """
    err_loc = cursor.location
    print "cursor", cursor.spelling, "file", err_loc.file
    print "usr", cursor.get_usr()
    print "line", err_loc.line, "col", err_loc.column


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
    def from_clang_cursor(cursor, proj_engine):
        assert cursor.location.file is not None
        return File.from_clang_tu(cursor.translation_unit,
                                  cursor.location.file.name, proj_engine)
    
    @staticmethod
    def from_clang_tu(tu, name, proj_engine):
        clang_file = tu.get_file(name)
        try:
            _file = proj_engine.get_session().query(File).\
                filter(File.name == clang_file.name).one()
        except MultipleResultsFound, e:
            print e
            raise
        except NoResultFound: # The file has not been stored in DB.
            _file = File(clang_file)
            print "adding file %s to DB" % clang_file.name
            proj_engine.get_session().add(_file)
            _file.includes = []
            for include in tu.get_includes():
                if include.source.name == _file.name:
                    _file.includes.append(
                        File.from_clang_tu(
                            tu, include.include.name, proj_engine))
        
        return _file

    @staticmethod
    def _is_file_in_db(file_name, proj_engine):
        try:
            files = proj_engine.get_session().query(File).\
                filter(File.name == file_name).all()
            return len(files) > 0
        except:
            return False

    @staticmethod
    def get_pending_filenames(tu, proj_engine):
        pending_files = set()
        for include in tu.get_includes():
            for file_name in [include.source.name, include.include.name]:
                if not File._is_file_in_db(file_name, proj_engine):
                    pending_files.add(file_name)

        if not File._is_file_in_db(tu.spelling, proj_engine):
            pending_files.add(tu.spelling)

        return pending_files
        

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
    kind = relationship('CursorKind')

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

    # lexical parent
    lexical_parent_id = Column(Integer, ForeignKey(id))
    lexical_parent = relationship("Cursor",
                                  foreign_keys=[lexical_parent_id],
                                  remote_side=[id])

    # semantic parent
    semantic_parent_id = Column(Integer, ForeignKey(id))
    semantic_parent = relationship("Cursor",
                                   foreign_keys=[semantic_parent_id],
                                   remote_side=[id])

    # referenced
    referenced_id = Column(Integer, ForeignKey(id))
    referenced = relationship("Cursor",
                              foreign_keys=[referenced_id],
                              remote_side=[id])
    
    # nested set attributes
    left = Column("left", Integer, nullable=True)
    right = Column("right", Integer, nullable=True)

    
    def __init__(self, cursor, proj_engine):
        self.spelling = cursor.spelling
        self.displayname = cursor.displayname
        self.usr = cursor.get_usr()
        self.is_definition = cursor.is_definition()
        self.is_static_method = cursor.is_static_method()

        location_start = cursor.location
        location_end = cursor.extent.end

        _print_error_cursor(cursor)

        self.location_start = SourceLocation(location_start.line,
                                             location_start.column,
                                             location_start.offset)
        self.location_end = SourceLocation(location_end.line,
                                           location_end.column,
                                           location_end.offset)

        self.kind = \
            CursorKind.from_clang_cursor_kind(cursor.kind, proj_engine)

        if cursor.location.file:
            self.file = File.from_clang_cursor(cursor, proj_engine)
    

    @staticmethod
    def from_clang_declaration(cursor, proj_engine):
        # if the cursor itself is a definition, then find out all the declaration cursors
        # that refer to it.
        # if the cursor is a declaration, then get the definition cursor

        assert cursor.is_definition()
        if cursor.get_usr() == "": # builtin definitions
            return None
        
        try:
            _cursor = proj_engine.get_session().query(Cursor).join(File).\
                filter(Cursor.usr == cursor.get_usr()).\
                filter(Cursor.is_definition == True).\
                filter(File.name == cursor.location.file.name).\
                filter(Cursor.offset_start == cursor.location.offset).one()
        except MultipleResultsFound, e:
            print e
            _print_error_cursor(cursor)
            raise
        except NoResultFound: # The cursor has not been stored in DB.
            _cursor = None

        return _cursor

    @staticmethod
    def from_definition(cursor, proj_engine):
        assert cursor.is_definition
        try:
            _cursors = proj_engine.get_session().query(Cursor).\
                filter(Cursor.usr == cursor.usr).\
                filter(Cursor.is_definition == False).all()
        except MultipleResultsFound, e:
            print e
            raise
        except NoResultFound: # The cursor has not been stored in DB.
            _cursors = []

        for _cursor in _cursors:
            _cursor.definition = cursor

        proj_engine.get_session().add_all(_cursors)
        
    @staticmethod
    def from_clang_cursor(cursor, proj_engine):
        """ Static method to create a cursor from libclang's cursor
        
        Arguments:
        - `cursor`:
        """
        if cursor.kind in [ckind.PAREN_EXPR, ckind.BINARY_OPERATOR,
                           ckind.BINARY_OPERATOR, ckind.COMPOUND_ASSIGNMENT_OPERATOR,
                           ckind.CONDITIONAL_OPERATOR, ckind.UNEXPOSED_EXPR]:
            return Cursor(cursor, proj_engine)

        try:
            # builtin definitions
            if cursor.location.file is None:
                _cursor = proj_engine.get_session().query(Cursor).\
                    filter(Cursor.spelling == cursor.spelling).one()
            else:
                _cursor = proj_engine.get_session().query(Cursor).\
                    join(File).join(CursorKind).\
                    filter(Cursor.usr == cursor.get_usr()).\
                    filter(Cursor.spelling == cursor.spelling).\
                    filter(Cursor.displayname == cursor.displayname).\
                    filter(CursorKind.name == cursor.kind.name).\
                    filter(File.name == cursor.location.file.name).\
                    filter(Cursor.offset_start == cursor.location.offset).\
                    filter(Cursor.offset_end == cursor.extent.end.offset).one()
        except MultipleResultsFound, e:
            print e
            _print_error_cursor(cursor)
            raise
        except NoResultFound: # The cursor has not been stored in DB.
            print "No result found"
            _cursor = Cursor(cursor, proj_engine)

        return _cursor

    @staticmethod
    def from_clang_referenced(cursor, proj_engine):
        assert(cursor.spelling is not None)
        
        # because referenced cursor will certainly have spelling, so I use spelling.
        try:
            _cursor = proj_engine.get_session().query(Cursor).join(File).\
                filter(Cursor.usr == cursor.get_usr()).\
                filter(File.name == cursor.location.file.name).\
                filter(Cursor.offset_start == cursor.location.offset).one()
        except MultipleResultsFound, e:
            print e
            _print_error_cursor(cursor)
            raise
        except NoResultFound: # The cursor has not been stored in DB.
            _cursor = Cursor(cursor, proj_engine)

        return _cursor

    @staticmethod
    def get_max_nested_set_index(proj_engine):
        """ Get the max value of right index for nested set model in DB.
        """

        max_right = proj_engine.get_session().\
            query(func.max(Cursor.right)).scalar()
        return max_right if max_right is not None else 0
 
        
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
    def from_clang_cursor_kind(kind, proj_engine):
        return proj_engine.get_session().query(CursorKind).\
            filter(CursorKind.name == kind.name).one()
    

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
    def from_clang_type(cursor_type, proj_engine):
        try:
            _type = proj_engine.get_session().query(Type).join(TypeKind).\
                filter(TypeKind.name == cursor_type.kind.name).\
                filter(Type.spelling == cursor_type.spelling).\
                filter(Type.is_const_qualified ==
                       cursor_type.is_const_qualified()).one()
        except MultipleResultsFound, e:
            print e
            raise
        except NoResultFound: # The type has not been stored in DB.
            _type = Type(cursor_type)
            _type.kind = \
                TypeKind.from_clang_type_kind(cursor_type.kind, proj_engine)

        # take care for the BLOCKPOINTER
        if cursor_type.kind == clang.cindex.TypeKind.POINTER:
            _type.pointee = \
                Type.from_clang_type(cursor_type.get_pointee(), proj_engine)
            
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
    def from_clang_type_kind(type_kind, proj_engine):
        """ Get the DB TypeKind from clang's TypeKind
        
        Arguments:
        - `type_kind`:
        """

        query = proj_engine.get_session().query(TypeKind).\
            filter(TypeKind.name == type_kind.name)
        return query.first()
        

