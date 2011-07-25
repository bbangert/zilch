"""SQLAlchemy Storage Backend"""
import base64
import datetime
import math
import logging

import simplejson

from sqlalchemy import create_engine
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import Table
from sqlalchemy import text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship
from sqlalchemy.types import DateTime
from sqlalchemy.types import Float
from sqlalchemy.types import Integer
from sqlalchemy.types import Text
from sqlalchemy.types import TypeDecorator


log = logging.getLogger(__name__)

Base = declarative_base()
Session = scoped_session(sessionmaker(expire_on_commit=False))


# Traversal objects
class Root(object):
    __name__ = ''
    __parent__ = None
    
    @property
    def object_keys(self):
        return {
            'event': Event,
            'event_type': EventType,
            'group': Group,
            'tag': Tag,
        }
    
    def __init__(self, request):
        self.request = request
    
    def __getitem__(self, name):
        obj = self.object_keys.get(name)
        if obj:
            ctx = DatabaseTable(obj)
            ctx.__parent__ = self
            ctx.__name__ = name
            return ctx
        else:
            raise KeyError()


class DatabaseTable(object):
    def __init__(self, object):
        self.table = object
    
    def __getitem__(self, key):
        table = self.table
        db_key = getattr(table, table.key_lookup)
        ctx = Session.query(table).filter(db_key==key).first()
        if ctx:
            ctx.__parent__ = self
            ctx.__name__ = key
            return ctx
        else:
            raise KeyError()


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
    key_lookup = 'id'
    
    @classmethod
    def get_or_create(cls, **kwargs):
        defaults = kwargs.pop('defaults', {})
        obj = Session.query(cls).filter_by(**kwargs).first()
        if not obj:
            kwargs.update(defaults)
            obj = cls(**kwargs)
            Session.add(obj)
            Session.commit()
            obj = Session.query(cls).filter_by(**kwargs).first()
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
    key_lookup = 'event_id'
    
    event_id = Column(Text, primary_key=True)
    type_id = Column(Integer, ForeignKey('event_type.id', ondelete='RESTRICT'))
    
    hash = Column(Text, nullable=False, index=True)
    datetime = Column(DateTime, default=datetime.datetime.now, nullable=False)
    time_spent = Column(Integer)
    data = Column(GzippedJSON)
    
    tags = relationship('Tag', secondary=event_tags, backref='events')


class EventType(Base, HelperMixin):
    __tablename__ = 'event_type'
    key_lookup = 'name'
    
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
    events = relationship('Event', secondary=group_events, lazy='dynamic',
                          backref='groups')
    
    def generate_score(self):
        return int(math.log(self.count) * 600 + int(self.last_seen.strftime('%s')))
    
    def last_event(self):
        return self.events.order_by(Event.datetime.desc()).first()
    
    def all_tags(self):
        query = Session.query(Tag).join(Tag.events).join(Event.groups)
        return query.filter(Group.id==self.id).group_by(Tag.id, Tag.name, Tag.value).all()
    
    def latest_events(self):
        query = Session.query(Event.event_id, Event.datetime).join(Event.groups)
        query = query.filter(Group.id==self.id).order_by(Event.datetime.desc())
        query = query.limit(50)
        return query.all()
    
    @classmethod
    def recently_seen(cls, limit=20):
        return Session.query(cls).order_by(cls.last_seen.desc()).limit(limit)
    
    event_type = relationship(EventType)


class ExceptionCreator(object):
    @classmethod
    def create_from_message(cls, message, db_uri):
        data = message['data']
        date = datetime.datetime.strptime(message['date'], '%Y-%m-%dT%H:%M:%S.%f')
        level = int(data.get('level', 0))
        class_name = data.get('type')
        value = data.get('value', '')

        traceback = data.pop('traceback', None)

        hash = message['hash']
        group_message = data['message']

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

        if group.count == 0:
            group.count = 1
            group.score = int(math.log(1) * 600 + int(date.strftime('%s')))
        elif db_uri.startswith('postgres'):
            group.score = text('log(count) * 600 + last_seen::abstime::int')
        elif db_uri.startswith('mysql'):
            group.score = text('log(times_seen) * 600 + unix_timestamp(last_seen)')
        else:
            group.count = group.count or 0
            group.score = group.generate_score()
        group.last_seen = date

        # Atomically update the group count
        group.count = Group.count + 1

        data = {
            'frames': data.get('frames'),
            'versions': data.get('versions'),
            'type': class_name,
            'value': value,
            'extra': message.get('extra'),
            'traceback': traceback,
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
        Session.remove()
