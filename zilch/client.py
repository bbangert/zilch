"""Zilch Recording Client

Two main methods are exposed for reporting exceptions,
:func:`~zilch.client.capture_exception` and :func:`~zilch.client.capture`.

The manner of reporting the exception varies depending on the configuration.
There's two options available to report the data:

* ZeroMQ based transport to a central recorder
* Direct storage via a ``Store`` object

Zilch comes with an `SQLAlchemy <http://sqlalchemy.org/>`_ ``Store`` to stash
captured data in a relational database.

Before reporting exceptions or using the zilch Logger, the
connection string for ZeroMQ that refers to the recorder_host should be
configured::

 import zilch.client zilch.client.recorder_host = "tcp://localhost:5555"

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
from threading import local

try:
    import zmq
except ImportError:
    pass

from weberror.collector import collect_exception

from zilch.exc import ConfigurationError
from zilch.utils import dumps
from zilch.utils import lookup_versions
from zilch.utils import shorten
from zilch.utils import transform
from zilch.utils import update_frame_visibility


store = None
recorder_host = None
_zeromq_socket = local()
capture_tags = []


def get_socket():
    """ZeroMQ Socket

    Caches the ZeroMQ socket on the module.

    """
    if not recorder_host:
        raise ConfigurationError("Recorder host string not configured.")
    
    if not hasattr(_zeromq_socket, 'sock'):
        context = zmq.Context()
        zero_socket = context.socket(zmq.PUSH)
        zero_socket.connect(recorder_host)
        _zeromq_socket.sock = zero_socket
    return _zeromq_socket.sock


def send(**kwargs):
    """Send a message to the recorder
    
    If there is no recorder_host and ``zilch.client.store`` is not
    None, then it is assumed to be a valid Storage backend and will
    immediately recieve the message and be flushed.

    """
    if recorder_host:
        data = dumps(kwargs).encode('zlib')
        get_socket().send(data, flags=zmq.NOBLOCK)
    elif store:
        store.message_received(kwargs)
        store.flush()
    else:
        raise ConfigurationError("No Record host or Store configured.")


def capture_exception(event_type="Exception", exc_info=None, 
                      level=logging.ERROR, tags=None, extra=None):
    """Capture the current exception"""
    exc_info = exc_info or sys.exc_info()
    
    # Ensure that no matter what happens, we always del the exc_info
    try:
        collected = collect_exception(*exc_info)

        # Check to see if this hash has been reported past the threshold
        # TODO: Use this in the future
        # cur_sec = int(time.time())
        # capture_key = '%s %s' % (hash, cur_sec)
    
        frames = []
        update_frame_visibility(collected.frames)
        for frame in collected.frames:
            fdata = {
                'id': frame.tbid,
                'filename': frame.filename,
                'module': frame.modname or '?',
                'function': frame.name or '?',
                'lineno': frame.lineno,
                'vars': frame.locals,
                'context_line': frame.get_source_line(),
                'with_context': frame.get_source_line(context=5),
                'visible': frame.visible,
            }
            frames.append(fdata)
    
        data = {
            'value': transform(collected.exception_value),
            'type': collected.exception_type,
            'message': ''.join(collected.exception_formatted),
            'level': level,
            'frames': frames,
            'traceback': ''.join(traceback.format_exception(*exc_info)),
        }
        modules = [frame['module'] for frame in data['frames']]
        data['versions'] = lookup_versions(modules)
        return capture(event_type, tags=tags, data=data, extra=extra,
                       hash=collected.identification_code)
    finally:
        del exc_info
        if 'collected' in locals():
            del collected


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
