"""ZeroMQ Client

Before reporting exceptions or using the zilch Logger, the connection
string for ZeroMQ that refers to the collector should be configured::
    
    import zilch.client
    zilch.client.collector_host = "tcp://localhost:5555"

Exceptions can then be reported with capture_exception function::
    
    from zilch.client import capture_exception
    try:
        # do something that explodes
    except Exception, e:
        capture_exception()

"""
import datetime
import logging
import sys
import traceback
import uuid

import zmq
import simplejson

from zilch.exc import ConfigurationError
from zilch.utils import get_traceback_frames
from zilch.utils import lookup_versions
from zilch.utils import shorten
from zilch.utils import transform


collector_host = None
_zeromq_socket = None

def get_socket():
    """ZeroMQ Socket

    Caches the ZeroMQ socket on the module.

    """
    global _zeromq_socket
    if not collector_host:
        raise ConfigurationError("Collector host string not configured.")
    
    if not _zeromq_socket:
        context = zmq.Context()
        zero_socket = context.socket(zmq.PUSH)
        zero_socket.connect(collector_host)
        _zeromq_socket = zero_socket
    return _zeromq_socket


def send(**kwargs):
    data = simplejson.dumps(kwargs).encode('zlib')
    get_socket().send(data, flags=zmq.NOBLOCK)


def capture_exception(exc_info=None, level=logging.ERROR):
    """Capture the current exception"""
    exc_info = exc_info or sys.exc_info()
    exc_type, exc_value, exc_traceback = exc_info
    
    if exc_type and not isinstance(exc_type, str):
        exception_type = exc_type.__name__
        if exc_type.__module__ not in ('__builtin__', 'exceptions'):
            exception_type = exc_type.__module__ + '.' + exception_type
    else:
        exception_type = exc_type
    
    tb_message = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    data = {
        'value': transform(exc_value),
        'type': exception_type,
        'level': level,
        'frames': get_traceback_frames(exc_traceback),
        'traceback': tb_message,
    }
    modules = [frame['module'] for frame in data['frames']]
    data['versions'] = lookup_versions(modules)
    return capture('Exception', data=data)


def capture(event_type, data=None, date=None, time_spent=None,
            event_id=None, **kwargs):
    """Captures a message/event and sends it to the collector"""
    data = data or {}
    date = date or transform(datetime.datetime.now())
    
    # tags = tags or []
    # tags.append(('Host', socket.gethostname()))

    event_id = uuid.uuid4().hex
    
    # Shorten lists/strings
    for k, v in data.iteritems():
        data[k] = shorten(v)
        
    send(event_type=event_type, data=data, date=date, time_spent=time_spent,
         event_id=event_id, **kwargs)
    return event_id
