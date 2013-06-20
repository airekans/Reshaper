from sqlalchemy import (create_engine, Column, ForeignKey)
from sqlalchemy import Integer, String, Boolean
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base
import weakref

engine = create_engine('sqlite://', echo=True)
# engine = create_engine('sqlite://', echo=True)
Base = declarative_base()


class Cursor(Base):
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

    def __init__(self):
        pass

class Type(Base):
    "Type DB represention"

    __tablename__ = 'type'
    
    id = Column(Integer, primary_key = True)
    
    is_const_qualified = Column(Boolean, nullable = False)

    def __init__(self):
        pass
    

def main():
    " main entry point  "
    
    Base.metadata.create_all(engine) 

    Session = sessionmaker(bind=engine)
    session = Session()


    # cursor = Cursor(spelling="abc", displayname="abc", is_definition=True)
    # type_obj = Type(is_const_qualified=False)

    # cursor.type = type_obj

    # session.add(cursor)
    # session.commit()

    cursor1 = None
    for cursor in session.query(Cursor).order_by(Cursor.id):
        print cursor.type
        cursor1 = cursor

    print "query User.type"
    print

    type_ref = weakref.ref(cursor1.type)

    print "weakref", type_ref()

    session.expire(cursor1)

    print "after expire"
    print "weakref", type_ref()


    print cursor.type
    

# def build_db_tree(cursor, parent):
#     db_cursor = db.Cursor(cursor)
#     db_cursor.parent = parent

#     session.add(db_cursor)

#     for child in cursor.get_children():
#         build_db_tree(child, db_cursor)

#     session.expire(db_cursor)
    
    
if __name__ == '__main__':
    main()



