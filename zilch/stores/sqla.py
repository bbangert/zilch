import base64
import datetime
import logging

import simplejson

from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship
from sqlalchemy.types import DateTime
from sqlalchemy.types import Integer
from sqlalchemy.types import Text
from sqlalchemy.types import TypeDecorator


from zilch.utils import construct_checksum

log = logging.getLogger(__name__)

Base = declarative_base()
Session = scoped_session(sessionmaker())


class GzippedJSON(TypeDecorator):
    impl = Text
    
    def process_bind_param(self, value, dialect):
        if value:
            return base64.b64encode(simplejson.dumps(value).encode('zlib'))
        else:
            return base64.b64encode(simplejson.dumps(dict()).encode('zlib'))
    
    def process_result_value(self, value, dialect):
        if value:
            return simplejson.loads(base64.b64decode(value).decode('zlib'))
        else:
            return dict()
    
    def copy(self):
        return GzippedJSON(self.impl.length)


def init_db(uri, **kwargs):
    engine = create_engine(uri, **kwargs)
    Session.configure(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)


class Event(Base):
    __tablename__ = 'events'

    event_id = Column(UUID, primary_key=True)
    logger = Column(Text, default='root', index=True)
    level = Column(Integer, default=logging.ERROR, index=True)
    class_name = Column(Text, index=True)
    message = Column(Text)
    hash = Column(Text, nullable=False, index=True)
    message = Column(Text, nullable=False, index=True)
    datetime = Column(DateTime, default=datetime.datetime.now, nullable=False)
    time_spent = Column(Integer)
    data = Column(GzippedJSON)


class SQLAlchemyStore(object):
    def __init__(self, uri=None):
        init_db(uri)
    
    def message_received(self, message):
        data = message['data']
        level = int(data.get('level', 0))
        class_name = data.get('type')
        value = data.get('value', '')
        hash = construct_checksum(
            level=level,
            traceback=data.get('traceback'),
            class_name=class_name,
            message=value,
        )
        event = Event(
            event_id=message['event_id'],
            level=level,
            class_name=class_name,
            message=value,
            hash=hash,
            time_spent=message.get('time_spent'),
            data = {
                'frames': data.get('frames'),
                'versions': data.get('versions')
            }
        )
        Session.add(event)
    
    def flush(self):
        Session.commit()
