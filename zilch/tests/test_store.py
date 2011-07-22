# coding: utf-8
import unittest
from contextlib import contextmanager

import simplejson
from nose.tools import eq_
from mock import patch
from mock import Mock

import zmq

class TestStore(unittest.TestCase):
    def _makeCapture(self):
        from zilch.client import capture_exception
        return capture_exception
    
    def _makeSession(self):
        from zilch.store import Session
        return Session
    
    def _makeSAStore(self):
        from zilch.store import SQLAlchemyStore
        return SQLAlchemyStore
    
    def _makeGroup(self):
        from zilch.store import Group
        return Group


class TestEventRecord(TestStore):    
    def testStoreException(self):
        store = self._makeSAStore()('sqlite://')
        with patch('zilch.client.send') as mock_send:
            cap = self._makeCapture()                        
            try:
                fred = smith['no_name']
            except:
                cap()
            kwargs = mock_send.call_args[1]
        
        try:
            # For the simplejson serialization that happens
            jsonified = simplejson.loads(simplejson.dumps(kwargs))
            store.message_received(jsonified)
            store.flush()
        
            Session = self._makeSession()
            Group = self._makeGroup()
            group = Session.query(Group).all()[0]
        
            eq_(len(group.latest_events()), 1)
            tags = group.all_tags()
            eq_(len(tags), 1)
            eq_(tags[0].name, 'Hostname')
            eq_(kwargs['event_type'], 'Exception')
            last_event = group.last_event()
            last_frame = last_event.data['frames'][-1]
            eq_(last_frame['function'], 'testStoreException')
            eq_(last_frame['module'], 'zilch.tests.test_store')
        finally:
            Session.remove()
