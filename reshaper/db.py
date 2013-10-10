from sqlalchemy import create_engine, Column, ForeignKey
from sqlalchemy import Integer, String, Boolean, Enum
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm import composite
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.orm.util import object_state
from sqlalchemy.schema import Table
from sqlalchemy.sql import func
from clang.cindex import CursorKind as ckind
import clang.cindex
import os
from collections import deque


_Base = declarative_base()

class HanldedCursors(object):
    
    class EqCursor(object):
        def __init__(self, cursor):
            self.cursor = cursor
            self.__eq_func = self.normal_eq if cursor.location.file \
                                else self.builtin_eq
        
        def builtin_eq(self, other):
            return self.cursor.spelling == other.cursor.spelling
        
        def normal_eq(self, other):
            return self.cursor.get_usr() == other.cursor.get_usr() and \
                self.cursor.spelling == other.cursor.spelling and \
                self.cursor.displayname == other.cursor.displayname and \
                self.cursor.kind == other.cursor.kind and \
                self.cursor.is_definition() == other.cursor.is_definition() and\
                self.cursor.location.file.name == \
                    other.cursor.location.file.name and \
                self.cursor.location.offset == other.cursor.location.offset and\
                self.cursor.extent.end.offset == other.cursor.extent.end.offset
        
        def __eq__(self, other):
            return self.__eq_func(other)
    
    def __init__(self):
        self.__file_to_cursors = {}
    
    def add_cursor(self, cursor):
        if cursor is None:
            return
        eq_cursor = HanldedCursors.EqCursor(cursor)
        if cursor.location.file is None:
            if None not in self.__file_to_cursors:
                self.__file_to_cursors[None] = []
            self.__file_to_cursors[None].append(eq_cursor)
        else:
            file_name = cursor.location.file.name
            if file_name not in self.__file_to_cursors:
                self.__file_to_cursors[file_name] = []
            self.__file_to_cursors[file_name].append(eq_cursor)
        
    def __contains__(self, cursor):
        if cursor is None:
            return False
        eq_cursor = HanldedCursors.EqCursor(cursor)
        if cursor.location.file is None:
            return None in self.__file_to_cursors and \
                eq_cursor in self.__file_to_cursors[None]
        else:
            file_name = cursor.location.file.name
            return file_name in self.__file_to_cursors and \
                eq_cursor in self.__file_to_cursors[file_name]

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
        # In cindex, TypeKind id is not continuous.
        # 0 - 29 is the first part, 100 - 113 is the second part.
        all_kinds = [clang.cindex.TypeKind.from_id(_i) for _i in xrange(30)]
        all_kinds += [clang.cindex.TypeKind.from_id(_i)
                      for _i in xrange(100, 114)]

        self._session.add_all([TypeKind(kind) for kind in all_kinds])
        self._session.commit()

    def build_db_file(self, tu):
        for include in tu.get_includes():
            self._session.add(
                File.from_clang_tu(tu, include.source.name, self))

        self._session.add(File.from_clang_tu(tu, tu.spelling, self))
        self._session.commit()
    
    def build_cursor_tree(self, cursor, parent, left):
        if cursor.kind in [ckind.USING_DIRECTIVE, ckind.USING_DECLARATION]:
            print "skip using directive"
            return left
        elif cursor.location.file is None:
            print "skip builtin element"
            return left
        
        db_cursor = Cursor(cursor, self)
        db_cursor.parent = parent
        db_cursor.left = left
        
        self._session.add(db_cursor)
        
        # lexical parent
        lex_parent = cursor.lexical_parent
        if lex_parent and lex_parent.kind != ckind.TRANSLATION_UNIT:
            for lex_pa in self._lex_parents:
                if lex_pa == lex_parent:
                    db_cursor.lexical_parent = lex_pa.db_cursor
                    break
            assert db_cursor.lexical_parent
        
        # semantic parent
        sem_parent = cursor.semantic_parent
        if sem_parent and sem_parent.kind != ckind.TRANSLATION_UNIT:
            if lex_parent and lex_parent == sem_parent:
                db_cursor.semantic_parent = db_cursor.lexical_parent
            else:
                # TODO: add cache here
                tmp_cursor = TmpCursor(sem_parent, 'SEM_CURSOR',
                                       self, db_cursor=db_cursor)
                self._session.add(tmp_cursor)

        is_add_lex_parents = False
        child_left = left + 1
        if cursor.kind != ckind.TEMPLATE_TEMPLATE_PARAMETER:
            for child in cursor.get_children():
                if not is_add_lex_parents:
                    cursor.db_cursor = db_cursor
                    self._lex_parents.appendleft(cursor)
                    is_add_lex_parents = True
                
                if child.location.offset >= cursor.location.offset:
                    child_left = \
                        self.build_cursor_tree(child, db_cursor, child_left) + 1
        
        right = child_left
        db_cursor.right = right
        
        if is_add_lex_parents:
            self._lex_parents.popleft()
        
        # declaration can be updated in the final stage
        if Type.is_valid_clang_type(cursor.type): # this can be improved
            db_type = Type.from_clang_type(cursor.type, self)
            db_cursor.type = db_type
            decl_cursor = cursor.type.get_declaration()
            if decl_cursor.kind != ckind.NO_DECL_FOUND:
                type_state = object_state(db_type)
                if type_state.transient:
                    tmp_cursor = TmpCursor(decl_cursor, 'TYPE',
                                           self, type=db_type)
                    self._session.add(tmp_cursor)
            db_cursor.type = db_type
            self._session.add(db_type)
        
        # referenced cursor handling
        ref_cursor = cursor.referenced
        if ref_cursor is not None and \
           ref_cursor.location.file is not None and \
           (ref_cursor.location.file.name != cursor.location.file.name or \
            ref_cursor.location.offset != cursor.location.offset) and \
           ref_cursor.kind != ckind.TRANSLATION_UNIT:
            tmp_cursor = TmpCursor(ref_cursor, 'REF_CURSOR',
                                   self, db_cursor=db_cursor)
            self._session.add(tmp_cursor)

        return right

    def build_db_tree2(self, cursor):
        if isinstance(cursor, clang.cindex.TranslationUnit):
            cursor = cursor.cursor
            _tu = cursor
        else: # cursor
            _tu = cursor.translation_unit
        
        pending_files = File.get_pending_filenames(_tu, self)
        self.build_db_file(_tu) # TODO: This can be improved.

        self._lex_parents = deque()

        left = Cursor.get_max_nested_set_index(self)
        if left > 0:
            left += 20
        if cursor.kind == clang.cindex.CursorKind.TRANSLATION_UNIT:
            handled_cursors = HanldedCursors()
            for child in cursor.get_children():
                if child.location.file and \
                        child.location.file.name in pending_files and \
                        child not in handled_cursors:
                    left = self.build_cursor_tree(child, None, left) + 1
                    handled_cursors.add_cursor(child)
                    self._session.commit()
        else:
            self.build_cursor_tree(cursor, None, left)
            self._session.commit()
        
        # post processing
        self.post_db_update()
        
    def post_db_update(self):
        tmp_cursors = self._session.query(TmpCursor).all()
        for tmp_cursor in tmp_cursors:
            if tmp_cursor.tmp_type == 'SEM_CURSOR':
                db_cursor = tmp_cursor.cursor
                try:
                    sem_parent = Cursor.get_db_cursor(tmp_cursor, self)
                except MultipleResultsFound:
                    if tmp_cursor.spelling:
                        raise
                    else:
                        continue
                except NoResultFound:
                    sem_parent = Cursor(tmp_cursor, self)
                assert sem_parent
                db_cursor.semantic_parent = sem_parent
                self._session.add(db_cursor)
            elif tmp_cursor.tmp_type == 'TYPE':
                with self._session.no_autoflush:
                    db_type = tmp_cursor.type
                    decl_cursor = Cursor.get_db_cursor(tmp_cursor, self)
                    assert decl_cursor
                    db_type.declaration = decl_cursor
                self._session.add(db_type)
            elif tmp_cursor.tmp_type == 'REF_CURSOR':
                db_cursor = tmp_cursor.cursor
                try:
                ref_cursor = Cursor.from_clang_referenced(tmp_cursor, self)
                db_cursor.referenced = ref_cursor
                self._session.add(db_cursor)
            else:
                assert False
        
        self._update_declarations()
        
        self._session.commit()
        
    
    def _update_declarations(self):
        cursor_usrs = self._session.query(Cursor.usr).filter(Cursor.usr != '').\
                        filter(Cursor.is_definition == False).\
                        filter(Cursor.definition_id is None).distinct().all()
        with self._session.no_autoflush:
            for (usr,) in cursor_usrs:
                decls = \
                    self._session.query(Cursor).filter(Cursor.usr == usr).all()
                def_cursor = None
                for decl in decls:
                    if decls.is_definition:
                        def_cursor = decl
                        break
                
                if def_cursor:
                    for decl in decls:
                        if decl is not def_cursor:
                            decl.definition = def_cursor
                
                self._session.add_all(decls)
    
    def build_db_cursor(self, cursor, parent, left):
        if cursor.kind in [ckind.USING_DIRECTIVE,
                           ckind.USING_DECLARATION]:
            print "skip using directive"
            return left
        elif cursor.location.file is None:
            print "skip builtin element"
            return left
        
        db_cursor = Cursor.from_clang_cursor(cursor, self) # this can be skipped
        # lexical parent and semantic parent?
        db_cursor.parent = parent
        print "cursor_id", id(db_cursor), "parent_id", id(parent)
        db_cursor.left = left
        
        self._session.add(db_cursor)
        
        if Type.is_valid_clang_type(cursor.type): # this can be improved
            db_cursor.type = Type.from_clang_type(cursor.type, self)
            decl_cursor = cursor.type.get_declaration()
            if (db_cursor.type.declaration is None or \
                not db_cursor.type.declaration.is_definition) and \
                decl_cursor.kind != ckind.NO_DECL_FOUND:
                db_cursor.type.declaration = \
                    Cursor.from_clang_cursor(decl_cursor, self)
                self._session.add(db_cursor.type)

        # this happens very little, so no need to change
        def_cursor = cursor.get_definition()
        if def_cursor is not None:
            if cursor.is_definition():
                Cursor._update_declarations(db_cursor, self)
            else:
                db_cursor.definition = \
                    Cursor.get_definition(def_cursor, self)

        # this needs to be cached.
        refer_cursor = cursor.referenced
        if refer_cursor is not None and \
           refer_cursor.location.file is not None and \
           (refer_cursor.location.file.name != cursor.location.file.name or \
            refer_cursor.location.offset != cursor.location.offset) and \
           refer_cursor.kind != ckind.TRANSLATION_UNIT:
            db_cursor.referenced = \
                Cursor.from_clang_referenced(refer_cursor, self)

        child_left = left + 1
        if cursor.kind != ckind.TEMPLATE_TEMPLATE_PARAMETER:
            for child in cursor.get_children():
                child_left = \
                    self.build_db_cursor(child, db_cursor, child_left) + 1

        right = child_left
        db_cursor.right = right

        self._session.add(db_cursor)
#        self._session.commit()
#        self._session.expire(db_cursor)

        return right

    def build_db_tree(self, cursor):
        if isinstance(cursor, clang.cindex.TranslationUnit):
            cursor = cursor.cursor
            _tu = cursor
        else: # cursor
            _tu = cursor.translation_unit
        
        pending_files = File.get_pending_filenames(_tu, self)
        self.build_db_file(_tu) # TODO: This can be improved.

        left = Cursor.get_max_nested_set_index(self)
        if left > 0:
            left += 20
        if cursor.kind == clang.cindex.CursorKind.TRANSLATION_UNIT:
            for child in cursor.get_children():
                if child.location.file and \
                        child.location.file.name in pending_files:
                    left = self.build_db_cursor(child, None, left) + 1
                    self._session.commit()
        else:
            self.build_db_cursor(cursor, None, left)
            self._session.commit()


def _print_error_cursor(cursor):
    """ print the information about cursor when error occur.
    
    Arguments:
    - `cursor`:
    """
    err_loc = cursor.location
    print "cursor", cursor.spelling, "file", err_loc.file
    print "usr", cursor.get_usr()
    print "line", err_loc.line, "col", err_loc.column


class File(_Base):
    """ DB representation for c++ files.
    """

    __tablename__ = 'file'

    id = Column(Integer, primary_key = True)
    
    name = Column(String, nullable = False)
    time = Column(Integer, nullable = False)

    include_table = Table('file_inclusion', _Base.metadata,
                              Column('including_id', Integer,
                                     ForeignKey('file.id')),
                              Column('included_id', Integer,
                                     ForeignKey('file.id')))
    includes = relationship("File",
                            secondary = include_table,
                            backref = "included_by",
                            primaryjoin = (id == include_table.c.including_id),
                            secondaryjoin = (id == include_table.c.included_id))
    
    
    def __init__(self, clang_file):
        """
        
        Arguments:
        - `clang_file`:
        """
        self.name = os.path.normpath(clang_file.name)
        self.time = clang_file.time
    
    def __str__(self):
        return self.name

    @staticmethod
    def from_clang_cursor(cursor, proj_engine):
        assert cursor.location.file is not None
        return File.from_clang_tu(cursor.translation_unit,
                                  cursor.location.file.name, proj_engine)
    
    @staticmethod
    def from_clang_tu(tu, name, proj_engine):
        clang_file = tu.get_file(name)
        file_name = os.path.normpath(clang_file.name)
        try:
            _file = proj_engine.get_session().query(File).\
                filter(File.name == file_name).one()
        except MultipleResultsFound, e:
            print e
            raise
        except NoResultFound: # The file has not been stored in DB.
            _file = File(clang_file)
            print "adding file %s to DB" % file_name
            proj_engine.get_session().add(_file)
            _file.includes = []
            for include in tu.get_includes():
                if os.path.normpath(include.source.name) == _file.name:
                    _file.includes.append(
                        File.from_clang_tu(
                            tu, include.include.name, proj_engine))
        
        return _file

    @staticmethod
    def _is_file_in_db(file_name, proj_engine):
        try:
            files = proj_engine.get_session().query(File).\
                filter(File.name == os.path.normpath(file_name)).all()
            return len(files) > 0
        except:
            return False

    @staticmethod
    def get_pending_filenames(tu, proj_engine):
        pending_files = set()
        for include in tu.get_includes():
            for file_name in [include.source.name, include.include.name]:
                if not File._is_file_in_db(file_name, proj_engine):
                    pending_files.add(os.path.normpath(file_name))

        if not File._is_file_in_db(tu.spelling, proj_engine):
            pending_files.add(os.path.normpath(tu.spelling))

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
    
    def __str__(self):
        return 'line %d col %d' % (self.line, self.column)


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
    type = relationship('Type', foreign_keys=[type_id])

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
    definition = relationship("Cursor",
                              # cascade deletions
                              cascade="all",
                              foreign_keys=[definition_id],
                              remote_side=[id])

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
    referenced_id = Column(Integer, ForeignKey(id, use_alter=True,
                                               name='cursor_ref'))
    referenced = relationship("Cursor",
                              foreign_keys=[referenced_id],
                              remote_side=[id], post_update=True)
    
    # TODO: add underlying_typedef here
    
    # nested set attributes
    left = Column("left", Integer, nullable=True)
    right = Column("right", Integer, nullable=True)

    def __init__(self, cursor, proj_engine):
        self.spelling = cursor.spelling
        self.displayname = cursor.displayname
        self.usr = cursor.get_usr()
        self.is_definition = cursor.is_definition()
        self.is_static_method = cursor.is_static_method()

        if cursor.get_usr() == 'c:@N@std@F@__throw_out_of_range#*1C#':
            import ipdb
            ipdb.set_trace()

        location_start = cursor.location
        location_end = cursor.extent.end

        _print_error_cursor(cursor)

        self.location_start = SourceLocation(location_start.line,
                                             location_start.column,
                                             location_start.offset)
        self.location_end = SourceLocation(location_end.line,
                                           location_end.column,
                                           location_end.offset)

        with proj_engine.get_session().no_autoflush:
            self.kind = \
                CursorKind.from_clang_cursor_kind(cursor.kind, proj_engine)
    
            if cursor.location.file:
                if isinstance(cursor, TmpCursor):
                    self.file = cursor.file
                else:
                    self.file = File.from_clang_cursor(cursor, proj_engine)

    @staticmethod
    def get_definition(cursor, proj_engine):
        # if the cursor itself is a definition, then find out all the declaration cursors
        # that refer to it.
        # if the cursor is a declaration, then get the definition cursor

        assert cursor.is_definition()
        if cursor.get_usr() == "": # builtin definitions
            return None
        
        try:
            _cursor = Cursor._query_one_cursor(cursor, proj_engine)
        except MultipleResultsFound, e:
            print e
            _print_error_cursor(cursor)
            raise
        except NoResultFound: # The cursor has not been stored in DB.
            _cursor = None

        return _cursor

    @staticmethod
    def _update_declarations(cursor, proj_engine):
        ''' Update the declarations in the DB with the definition.
        
        `cursor`: the definition cursor
        '''
        
        assert cursor.is_definition

        _cursors = proj_engine.get_session().query(Cursor).\
            filter(Cursor.usr == cursor.usr).\
            filter(Cursor.spelling == cursor.spelling).\
            filter(Cursor.is_definition == False).all()

        for _cursor in _cursors:
            _cursor.definition = cursor

        proj_engine.get_session().add_all(_cursors)
    
    @staticmethod
    def _get_cursor_query(cursor, proj_engine):
        return proj_engine.get_session().query(Cursor).\
                    join(File).join(CursorKind).\
                    filter(Cursor.usr == cursor.get_usr()).\
                    filter(Cursor.spelling == cursor.spelling).\
                    filter(Cursor.displayname == cursor.displayname).\
                    filter(CursorKind.name == cursor.kind.name).\
                    filter(Cursor.is_definition == cursor.is_definition()).\
                    filter(File.name == cursor.location.file.name).\
                    filter(Cursor.offset_start == cursor.location.offset).\
                    filter(Cursor.offset_end == cursor.extent.end.offset)

    @staticmethod
    def _query_cursors(cursor, proj_engine):
        return Cursor._get_cursor_query(cursor, proj_engine).all()
    
    @staticmethod
    def _query_one_cursor(cursor, proj_engine):
        return Cursor._get_cursor_query(cursor, proj_engine).one()
    
    @staticmethod
    def from_clang_cursor(cursor, proj_engine):
        """ Static method to create a cursor from libclang's cursor
        
        Arguments:
        - `cursor`:
        """
        if not cursor.spelling and not cursor.get_usr() and \
            cursor.kind != ckind.OVERLOADED_DECL_REF:
            return Cursor(cursor, proj_engine)

        try:
            _cursor = Cursor.get_db_cursor(cursor, proj_engine)
        except NoResultFound: # The cursor has not been stored in DB.
            print "No result found"
            _cursor = Cursor(cursor, proj_engine)

        return _cursor
    
    @staticmethod
    def get_db_cursors(cursor, proj_engine):
        if cursor.location.file is None:
            _cursors = proj_engine.get_session().query(Cursor).\
                filter(Cursor.spelling == cursor.spelling).all()
        else:
            _cursors = Cursor._query_cursors(cursor, proj_engine)
        return _cursors
    
    @staticmethod
    def get_db_cursor(cursor, proj_engine):
        # builtin definitions
        try:
            if cursor.location.file is None:
                _cursor = proj_engine.get_session().query(Cursor).\
                    filter(Cursor.spelling == cursor.spelling).one()
            else:
                _cursor = Cursor._query_one_cursor(cursor, proj_engine)
            return _cursor
        except MultipleResultsFound, e:
            print e
            _print_error_cursor(cursor)
            raise

    @staticmethod
    def from_clang_referenced(cursor, proj_engine):
        try:
            _cursor = Cursor.get_db_cursor(cursor, proj_engine)
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


class TmpCursor(_Base):
    """ Temporary table for Cursor relationship.
    """
    
    __tablename__ = 'tmp_cursor'
    id = Column(Integer, primary_key = True)
    
    # following attributes are used to retrieve the cursors in the DB
    # You can think it as serialized cindex.Cursor.
    spelling = Column(String, nullable = True)
    displayname = Column(String, nullable = False)
    usr = Column(String, nullable = True)
    _is_definition = Column(Boolean, nullable = False)
    _is_static_method = Column(Boolean, nullable = False)

    tmp_type = Column(Enum('REF_CURSOR', 'SEM_CURSOR', 'TYPE',
                           name='tmp_type'),
                      nullable = False)

    kind_id = Column(Integer, ForeignKey('cursor_kind.id'))
    kind = relationship('CursorKind')
    
    file_id = Column(Integer, ForeignKey('file.id'))
    file = relationship("File")
    
    # only valid for TYPE
    type_id = Column(Integer, ForeignKey('type.id'))
    type = relationship('Type', foreign_keys=[type_id])

    # only valid for REF_CURSOR and SEM_CURSOR
    cursor_id = Column(Integer, ForeignKey('cursor.id'))
    cursor = relationship(Cursor, foreign_keys=[cursor_id])
    
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
    
    def __init__(self, cursor, tmp_type, proj_engine, **kws):
        self.spelling = cursor.spelling
        self.displayname = cursor.displayname
        self.usr = cursor.get_usr()
        self._is_definition = cursor.is_definition()
        self._is_static_method = cursor.is_static_method()

        location_start = cursor.location
        location_end = cursor.extent.end

        self.location_start = SourceLocation(location_start.line,
                                             location_start.column,
                                             location_start.offset)
        self.location_end = SourceLocation(location_end.line,
                                           location_end.column,
                                           location_end.offset)
        
        # disable autoflush
        with proj_engine.get_session().no_autoflush:
            self.kind = \
                CursorKind.from_clang_cursor_kind(cursor.kind, proj_engine)
    
            if cursor.location.file:
                self.file = File.from_clang_cursor(cursor, proj_engine)
        
        self.tmp_type = tmp_type
        if tmp_type == 'TYPE':
            self.type = kws['type']
        else:
            self.cursor = kws['db_cursor']
        
    # The following methods are adapters for cindex.Cursor
    def is_definition(self):
        return self._is_definition
    
    def is_static_method(self):
        return self._is_static_method
    
    def get_usr(self):
        return self.usr
    
    @property
    def location(self):
        if not hasattr(self, '_location'):
            self._location = lambda : True # empty object
            self._location.file = self.file
            self._location.line = self.location_start.line
            self._location.column = self.location_start.column
            self._location.offset = self.location_start.offset
        
        return self._location
    
    @property
    def extent(self):
        if not hasattr(self, '_extent'):
            self._extent = lambda : True
            self._extent.end = self.location_end
            
        return self._extent
        
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
    pointee = relationship("Type",
                        # One-to-One
                        uselist=False,
                        foreign_keys=[pointee_id],
                        remote_side=[id])

    kind_id = Column(Integer, ForeignKey("type_kind.id"))
    kind = relationship('TypeKind')

    declaration_id = Column(Integer,
                            ForeignKey("cursor.id", use_alter=True,
                                       name="type_decl"))
    declaration = relationship(Cursor, foreign_keys=[declaration_id],
                               post_update=True)
    

    def __init__(self, cursor_type, proj_engine):
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
        self.kind = TypeKind.from_clang_type_kind(cursor_type.kind, proj_engine)

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
            _type = Type(cursor_type, proj_engine)

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

        return proj_engine.get_session().query(TypeKind).\
            filter(TypeKind.name == type_kind.name).one()
        

