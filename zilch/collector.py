"""Zilch Collector"""
import time

import simplejson
import zmq


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
        print "Running zilch-collector on port: %s" % self.zeromq_bind
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
            if now - last_flush > 5 and messages:
                self.store.flush()
                last_flush = now
                messages = False
