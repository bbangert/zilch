"""ZeroMQ Reporter and Collector

Before reporting exceptions or using the zilch Logger, the connection
string for ZeroMQ that refers to the collector should be configured::
    
    import zilch
    zilch.Reporter.connection_string = "tcp://localhost:5555"

Exceptions can then be reported with capture_exception function::
    
    try:
        # do something that explodes
    except Exception, e:
        zilch.capture_exception()

"""
import base64
import datetime
import logging
import socket
import sys
import time
import traceback
import uuid

import zmq
import simplejson

from zilch.utils import construct_checksum
from zilch.utils import get_traceback_frames
from zilch.utils import lookup_versions
from zilch.utils import transform


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
        
    Reporter.send(event_type=event_type, data=data, date=date, 
                  time_spent=time_spent, event_id=event_id, **kwargs)
    return event_id
    

class Reporter(object):
    """ZeroMQ Reporter
    
    Before using the Reporter, configure the class by setting its
    connection string::
    
        import zilch
        zilch.Reporter.connection_string = "tcp://localhost:5555"
    
    """
    connection_string = None
    _zmq_socket = None

    @staticmethod
    def get_socket():
        """ZeroMQ Socket

        Caches the ZeroMQ socket on the class.

        """
        if not Reporter._zmq_socket:
            context = zmq.Context()
            zero_socket = context.socket(zmq.PUSH)
            zero_socket.connect(Reporter.connection_string)
            Reporter._zmq_socket = zero_socket
        return Reporter._zmq_socket
    
    @staticmethod
    def send(**kwargs):
        data = simplejson.dumps(kwargs).encode('zlib')
        Reporter.get_socket().send(data, flags=zmq.NOBLOCK)


class Collector(object):
    """ZeroMQ Collector
    
    The Collector by itself has no methodology to store data recieved
    over ZeroMQ, a ``store`` instance should be provided that
    implements a ``message_received`` and ``flush`` method.
    
    """
    _zmq_socket = None
    
    def __init__(self, zeromq_bind=None, store=None):
        self.zeromq_bind = zeromq_bind
        self.store = store
    
    @property
    def sock(self):
        """ZeroMQ Socket Property

        Caches the ZeroMQ socket on the class.

        """
        if not self._zmq_socket:
            context = zmq.Context()
            zero_socket = context.socket(zmq.PULL)
            zero_socket.bind(self.zeromq_bind)
            self._zmq_socket = zero_socket
        return self._zmq_socket
    
    def main_loop(self):
        """Run the main collector loop
        
        Every message recieved will result in ``message_recieved`` being
        called with the de-serialized JSON data.
        
        Every 10 seconds, the ``flush`` method will be called for storage
        instances that wish to flush collected messages periodically for
        efficiency. ``flush`` will *only* be called if there actually
        were messages in the prior 10 seconds.
        
        The main_loop executes in a serial single-threaded fashion.
        
        """
        messages = False
        now = time.time()
        last_flush = now
        while 1:
            try:
                message = self.sock.recv(flags=zmq.NOBLOCK)
                data = simplejson.loads(message.decode('zlib'))
                self.store.message_received(data)
                messages = True
            except zmq.ZMQError, e:
                if e.errno != zmq.EAGAIN:
                    raise
                time.sleep(0.2)
            now = time.time()
            if now - last_flush > 10 and messages:
                self.store.flush()
                last_flush = now
                messages = False
