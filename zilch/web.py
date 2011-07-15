"""Small Pyramid Web Application to view Event Database

Running the Zilch webapp requires Pyramid 1.0 or greater to be installed.

"""
from pyramid.config import Configurator
from pyramid.httpexceptions import HTTPFound
from pyramid.response import Response
from pyramid.view import view_config

from zilch.store import init_db
from zilch.store import Event
from zilch.store import EventType
from zilch.store import DatabaseTable
from zilch.store import Group
from zilch.store import Tag
from zilch.store import Root


# Views
@view_config(context=Root)
def home(request):
    return HTTPFound(location='/group/')


@view_config(context=DatabaseTable, path_info='/group/', renderer='/group/index.mak')
def group_index(context, request):
    return {'groups': Group.recently_seen()}


@view_config(context=Group, renderer='/group/show.mak')
def group_details(context, request):
    last_event = context.last_event()
    return {'last_event': context.last_event(), 'group': context}


def make_webapp(database_uri):
    init_db(database_uri)
    config = Configurator(root_factory=Root)
    config.add_settings({'mako.directories': 'zilch:templates/'})
    config.scan('zilch.web')
    config.add_static_view('css', 'zilch:static/css')
    config.add_static_view('images', 'zilch:static/images')
    
    app = config.make_wsgi_app()
    return app
