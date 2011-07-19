"""ZeroMQ Client

Before reporting exceptions or using the zilch Logger, the connection
string for ZeroMQ that refers to the recorder_host should be configured::
    
    import zilch.client
    zilch.client.recorder_host = "tcp://localhost:5555"

Exceptions can then be reported with capture_exception function::
    
    from zilch.client import capture_exception
    try:
        # do something that explodes
    except Exception, e:
        capture_exception()

To add process-wide tags that should be recorded for all events sent in the
current process::
    
    zilch.client.capture_tags.append(
        ('Application', 'My Awesome App')
    )

"""
import datetime
import logging
import socket
import sys
import traceback
import uuid

import zmq
import simplejson
from webob import Request
from webob import Response

from zilch.exc import ConfigurationError
from zilch.utils import construct_checksum
from zilch.utils import get_traceback_frames
from zilch.utils import lookup_versions
from zilch.utils import shorten
from zilch.utils import transform


recorder_host = None
_zeromq_socket = None
capture_tags = []


def get_socket():
    """ZeroMQ Socket

    Caches the ZeroMQ socket on the module.

    """
    global _zeromq_socket
    if not recorder_host:
        raise ConfigurationError("Collector host string not configured.")
    
    if not _zeromq_socket:
        context = zmq.Context()
        zero_socket = context.socket(zmq.PUSH)
        zero_socket.connect(recorder_host)
        _zeromq_socket = zero_socket
    return _zeromq_socket


def send(**kwargs):
    """Send a message over ZeroMQ"""
    data = simplejson.dumps(kwargs).encode('zlib')
    get_socket().send(data, flags=zmq.NOBLOCK)


def capture_exception(event_type="Exception", exc_info=None, 
                      level=logging.ERROR, tags=None, extra=None):
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

    # Check to see if this hash has been reported past the threshold
    # TODO: Use this in the future
    # hash = construct_checksum(
    #     level=level,
    #     class_name=exception_type,
    #     traceback=tb_message,
    #     message=transform(exc_value),
    # )
    # cur_sec = int(time.time())
    # capture_key = '%s %s' % (hash, cur_sec)
    
    data = {
        'value': transform(exc_value),
        'type': exception_type,
        'level': level,
        'frames': get_traceback_frames(exc_traceback),
        'traceback': tb_message,
    }
    modules = [frame['module'] for frame in data['frames']]
    data['versions'] = lookup_versions(modules)
    return capture(event_type, tags=tags, data=data, extra=extra)


def capture(event_type, tags=None, data=None, date=None, time_spent=None,
            event_id=None, extra=None, **kwargs):
    """Captures a message/event and sends it to the recorder
    
    :param event_type: the type of event, backend stores should be able to
                       handle the basic set of events ('Exception', 'Log')
    :param data: the data for this event
    :param date: the datetime of this event
    :param time_spent: a float value representing the duration of the event
    :param event_id: a 32-length unique string identifying this event
    :param extra: a dictionary of additional standard metadata
    :return: a 32-length string identifying this event
    
    """
    data = data or {}
    date = date or transform(datetime.datetime.utcnow())
    extra = extra or {}
    event_id = event_id or uuid.uuid4().hex
    
    tags = tags or []
    tags.extend(capture_tags)
    tags.append(('Hostname', socket.gethostname()))
    
    # Shorten lists/strings
    for k, v in data.items():
        if k in ['traceback', 'frames', 'versions']:
            data[k] = transform(v)
            continue
        data[k] = shorten(v)

    # Shorten extra
    for k, v in extra.items():
        extra[k] = shorten(v)
    
    send(event_type=event_type, tags=tags, data=data, date=date,
         time_spent=time_spent, event_id=event_id, extra=extra, **kwargs)
    return event_id
