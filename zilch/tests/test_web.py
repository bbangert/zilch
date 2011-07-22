# coding: utf-8
import unittest
from contextlib import contextmanager

import simplejson
from nose.tools import eq_
from mock import patch
from mock import Mock
from pyramid.testing import DummyRequest

import zmq

class TestWeb(unittest.TestCase):
    def setUp(self):
        store = self._makeSAStore()('sqlite://')
        with patch('zilch.client.send') as mock_send:
            cap = self._makeCapture()                        
            try:
                fred = smith['no_name']
            except:
                cap()
            kwargs = mock_send.call_args[1]
        jsonified = simplejson.loads(simplejson.dumps(kwargs))
        store.message_received(jsonified)
        store.flush()
    
    def tearDown(self):
        self._makeSession().remove()
    
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
    
    def test_home_redirect(self):
        from zilch.web import home
        req = DummyRequest()
        result = home(req)
        eq_(result.status_int, 302)

    def test_group_index(self):
        from zilch.web import group_index
        req = DummyRequest()
        result= group_index(None, req)
        eq_(len(result['groups']), 1)

    def test_group_view(self):
        from zilch.web import group_details
        req = DummyRequest()
        Group = self._makeGroup()
        Session = self._makeSession()
        group = Session.query(Group).all()[0]
        result = group_details(group, req)
        eq_(len(result['latest_events']), 1)
        