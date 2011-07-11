from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker


Base = declarative_base()
Session = scoped_session(sessionmaker())


def init_db(uri, **kwargs):
    engine = create_engine(uri, **kwargs)
    Session.configure(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)




class SQLAlchemyStore(object):
    def __init__(self, uri=None):
        init_db(uri)
