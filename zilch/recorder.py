"""Zilch Recorder"""
import time
import signal

try:
    import zmq
except:
    pass

from zilch.utils import loads

class Recorder(object):
    """ZeroMQ Recorder
    
    The Recorder by itself has no methodology to record data recieved
    over ZeroMQ, a ``store`` instance should be provided that
    implements a ``message_received`` and ``flush`` method.
    
    """
    def __init__(self, zeromq_bind=None, store=None):
        self.zeromq_bind = zeromq_bind
        self.store = store
        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGUSR1, self.shutdown)
        
        self._context = context = zmq.Context()
        zero_socket = context.socket(zmq.PULL)
        zero_socket.bind(self.zeromq_bind)
        self.sock = zero_socket
    
    def shutdown(self, signum, stack):
        """Shutdown the main loop and handle remaining messages"""
        self.sock.close()
        messages = True
        message_count = 0
        while messages:
            try:
                message = self.sock.recv(flags=zmq.NOBLOCK)
                data = loads(message.decode('zlib'))
                self.store.message_received(data)
                message_count += 1
            except zmq.ZMQError, e:
                messages = False
        if message_count:
            self.store.flush()
        self._context.term()
        raise SystemExit("Finished processing remaining messages, exiting.")
    
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
        print "Running zilch-recorder on port: %s" % self.zeromq_bind
        messages = False
        now = time.time()
        last_flush = now

        while 1:
            try:
                message = self.sock.recv(flags=zmq.NOBLOCK)
                data = loads(message.decode('zlib'))
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
