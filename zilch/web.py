"""Small Pyramid Web Application to view Event Database

Running the Zilch webapp requires Pyramid 1.0 or greater to be installed.

"""
import pytz
from pyramid.config import Configurator
from pyramid.decorator import reify
from pyramid.events import NewRequest
from pyramid.events import subscriber
from pyramid.httpexceptions import HTTPFound
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_config

from zilch.store import init_db
from zilch.store import Session
from zilch.store import Event
from zilch.store import EventType
from zilch.store import DatabaseTable
from zilch.store import Group
from zilch.store import Tag
from zilch.store import Root

@subscriber(NewRequest)
def session_cleanup(event):
    event.request.add_finished_callback(lambda x: Session.remove())


@view_config(context=Root)
def home(request):
    return HTTPFound(location=request.application_url + '/group/')


@view_config(context=DatabaseTable, path_info='/group/', renderer='/group/index.mak')
def group_index(context, request):
    groups = list(Group.recently_seen())
    for group in groups:
        tags = ['%s:%s' % (tag.name, tag.value) for tag in group.all_tags()]
        group.tags = ' '.join(tags)
    return {'groups': groups}


@view_config(context=Group, renderer='/group/show.mak')
@view_config(context=Group, name='event', renderer='/group/show.mak')
def group_details(context, request):
    if request.subpath:
        event_id = request.subpath[0]
        event = Session.query(Event).filter_by(event_id=event_id).one()
    else:
        event = context.last_event()
    event_type = context.event_type
    latest_events = context.latest_events()
    return {'event': event, 'group': context, 'latest_events': latest_events,
            'event_type': event_type}


class RequestWithTimezone(Request):
    _default_timezone = ''
    
    @reify
    def timezone(self):
        tzinfo = self._default_timezone or UTC
        if isinstance(tzinfo, basestring):
            tzinfo = pytz.timezone(tzinfo)
        return tzinfo


def make_webapp(database_uri, default_timezone=None):
    init_db(database_uri)
    config = Configurator(root_factory=Root)
    RequestWithTimezone._default_timezone = default_timezone
    config.set_request_factory(RequestWithTimezone)
    config.add_settings(
        {'mako.directories': 'zilch:templates/',
        'mako.default_filters': 'h'},
    )
    config.add_static_view('stylesheets', 'zilch:static/stylesheets')
    config.add_static_view('images', 'zilch:static/images')
    config.add_static_view('javascripts', 'zilch:static/javascripts')
    config.scan('zilch.web')
    
    app = config.make_wsgi_app()
    return app
