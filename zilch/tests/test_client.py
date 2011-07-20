import unittest
from contextlib import contextmanager

from nose.tools import eq_
from mock import patch
from mock import Mock

import zmq

@contextmanager
def client_recorder(host):
    import zilch.client
    prior = zilch.client.recorder_host
    zilch.client.recorder_host = host
    try:
        yield
    finally:
        zilch.client.recorder_host = prior


class TestSend(unittest.TestCase):
    def _makeOne(self):
        from zilch.client import send
        return send
    
    def test_send(self):
        with patch('zilch.client.get_socket', spec=zmq.Context) as mock:
            mock_socket = Mock()
            mock.return_value = mock_socket
            send = self._makeOne()
            send(test='data')
            eq_(mock.call_count, 1)
            eq_(mock_socket.method_calls[0][0], 'send')

class TestGetSocket(unittest.TestCase):
    def _makeOne(self):
        from zilch.client import get_socket
        return get_socket
    
    def test_get_socket(self):
        with patch('zmq.Context') as mock:
            mock_context = Mock()
            mock.return_value = mock_context
            get_sock = self._makeOne()
            
            with client_recorder('localhost'):
                sock = get_sock()
            eq_(mock_context.method_calls[0][0], 'socket')


class TestCapture(unittest.TestCase):
    def _makeOne(self):
        from zilch.client import capture_exception
        return capture_exception
    
    def test_capture_exc(self):
        with patch('zilch.client.send') as mock_send:
            cap = self._makeOne()
            try:
                fred = smith['no_name']
            except:
                cap()
            kwargs = mock_send.call_args[1]
            eq_(kwargs['event_type'], 'Exception')
            last_frame = kwargs['data']['frames'][-1]
            eq_(last_frame['function'], 'test_capture_exc')
            eq_(last_frame['module'], 'zilch.tests.test_client')
