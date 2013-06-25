from sqlalchemy import create_engine, Column, ForeignKey
from sqlalchemy import Integer, String, Boolean
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.collections import attribute_mapped_collection
import weakref


_engine = create_engine('sqlite:///test.db', echo=True)
_Base = declarative_base()


class Cursor(_Base):
    " Cursor DB representation  "
    
    __tablename__ = 'cursor'

    id = Column(Integer, primary_key = True)
    spelling = Column(String, nullable = True)
    displayname = Column(String, nullable = False)
    usr = Column(String, nullable = True)
    is_definition = Column(Boolean, nullable = False)

    type_id = Column(Integer, ForeignKey('type.id'))
    type = relationship('Type',
                        backref = backref('instances', order_by = id))

    parent_id = Column(Integer, ForeignKey(id))
    children = relationship("Cursor",

                        # cascade deletions
                        cascade="all",

                        # many to one + adjacency list - remote_side
                        # is required to reference the 'remote'
                        # column in the join condition.
                        backref=backref("parent", remote_side=id),

                        # children will be represented as a dictionary
                        # on the "name" attribute.
                        collection_class=attribute_mapped_collection('name'),
                    )

    def __init__(self, spelling, displayname, usr, is_definition):
        self.spelling = spelling
        self.displayname = displayname
        self.usr = usr
        self.is_definition = is_definition

    @classmethod
    def from_clang_cursor(cls, cursor):
        """ Static method to create a cursor from libclang's cursor
        
        Arguments:
        - `cursor`:
        """

        return cls(cursor.spelling, cursor.displayname,
                   cursor.get_usr(), cursor.is_definition())

        
        

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

    def build_db_cursor(cursor, parent):
        db_cursor = Cursor.from_clang_cursor(cursor)
        db_cursor.parent = parent

        _session.add(db_cursor)
        _session.commit()

        for child in cursor.get_children():
            build_db_cursor(child, db_cursor)

        _session.expire(db_cursor)
    
    build_db_cursor(cursor, None)
    

