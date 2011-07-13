"""SQLAlchemy Storage Backend"""
import base64
import datetime
import hashlib
import math
import logging

import simplejson

from sqlalchemy import create_engine
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import Table
from sqlalchemy import text
from sqlalchemy import func
from sqlalchemy import UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship
from sqlalchemy.types import DateTime
from sqlalchemy.types import Float
from sqlalchemy.types import Integer
from sqlalchemy.types import Text
from sqlalchemy.types import TypeDecorator


from zilch.utils import construct_checksum

log = logging.getLogger(__name__)

Base = declarative_base()
Session = scoped_session(sessionmaker())


class GzippedJSON(TypeDecorator):
    """Implements a gzipped JSON type to store additional event
    information"""
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
    """Initialize the Session and create the database tables if
    necessary"""
    engine = create_engine(uri, **kwargs)
    Session.configure(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)


class HelperMixin(object):
    @classmethod
    def get_or_create(cls, **kwargs):
        defaults = kwargs.pop('defaults', {})
        obj = Session.query(cls).filter_by(**kwargs).first()
        if not obj:
            kwargs.update(defaults)
            obj = cls(**kwargs)
            Session.add(obj)
            Session.flush()
        return obj


class Tag(Base, HelperMixin):
    __tablename__ = 'tag'

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, index=True)
    value = Column(Text, nullable=False)

Index('idx_name_value', Tag.name, Tag.value, unique=True)


event_tags = Table(
    'event_tags', Base.metadata,
    Column('event_id', Text, ForeignKey('event.event_id', ondelete='CASCADE')),
    Column('tag_id', Integer, ForeignKey('tag.id', ondelete='RESTRICT'))
)


class Event(Base, HelperMixin):
    __tablename__ = 'event'
    
    event_id = Column(Text, primary_key=True)
    type_id = Column(Integer, ForeignKey('event_type.id', ondelete='RESTRICT'))
    
    hash = Column(Text, nullable=False, index=True)
    datetime = Column(DateTime, default=datetime.datetime.now, nullable=False)
    time_spent = Column(Integer)
    data = Column(GzippedJSON)
    
    tags = relationship('Tag', secondary=event_tags)


class EventType(Base, HelperMixin):
    __tablename__ = 'event_type'
    
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, index=True)


group_events = Table(
    'group_events', Base.metadata,
    Column('group_id', Integer, ForeignKey('group.id', ondelete='CASCADE')),
    Column('event_id', Text, ForeignKey('event.event_id', ondelete='CASCADE'))
)


class Group(Base, HelperMixin):
    __tablename__ = 'group'

    id = Column(Integer, primary_key=True)
    type_id = Column(Integer, ForeignKey('event_type.id', ondelete='RESTRICT'))

    # this is the combination of md5(' '.join(tags)) + md5(event)
    hash = Column(Text)

    # One-line summary used for display purposes
    message = Column(Text, nullable=False)

    count = Column(Integer, default=0, nullable=False)
    state = Column(Integer, default=1)
    last_seen = Column(DateTime, default=datetime.datetime.now, nullable=False)
    first_seen = Column(DateTime, default=datetime.datetime.now, nullable=False)

    score = Column(Float, default=0)
    events = relationship('Event', secondary=group_events, backref='groups')
    
    def generate_score(self):
        return int(math.log(self.count) * 600 + int(self.last_seen.strftime('%s')))


class ExceptionCreator(object):
    @classmethod
    def create_from_message(cls, message, db_uri):
        data = message['data']
        date = message['date']
        level = int(data.get('level', 0))
        class_name = data.get('type')
        value = data.get('value', '')

        traceback = data.pop('traceback', None)

        hash = construct_checksum(
            level=level,
            traceback=traceback,
            class_name=class_name,
            message=value,
        )
        group_message = '%s: %s' % (class_name, value)

        event_type = EventType.get_or_create(name=message['event_type'])
        tags = [Tag.get_or_create(name=x, value=y) for x,y in message.get('tags', [])]

        group = Group.get_or_create(
            type_id=event_type.id,
            hash=hash,
            defaults=dict(
                message=group_message,
                first_seen=date,
                last_seen=date)
        )
        group.last_seen = date

        # Atomically update the group count
        group.count = Group.count + 1
        if db_uri.startswith('postgres'):
            group.score = text('log(count) * 600 + last_seen::abstime::int')
        elif db_uri.startswith('mysql'):
            group.score = text('log(times_seen) * 600 + unix_timestamp(last_seen)')
        else:
            group.count = group.count or 0
            group.score = Group.generate_score()

        data = {
            'frames': data.get('frames'),
            'versions': data.get('versions'),
            'type': class_name,
            'value': value,
            'extra': message.get('extra'),
        }

        event = Event(
            hash=hash,
            type_id=event_type.id,
            event_id=message['event_id'],
            datetime=date,
            data=data,
            time_spent=message['time_spent'],
        )
        event.groups.append(group)
        for tag in tags:
            event.tags.append(tag)
        return event


event_classes = {
    'Exception': ExceptionCreator,
    'HTTPException': ExceptionCreator,
}


class SQLAlchemyStore(object):
    def __init__(self, uri=None):
        init_db(uri)
        self.uri = uri

    def message_received(self, message):
        EventClass = event_classes.get(message['event_type'])
        if EventClass:
            event = EventClass.create_from_message(message, self.uri)
            Session.add(event)

    def flush(self):
        Session.commit()
