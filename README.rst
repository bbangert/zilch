=====
zilch
=====

``zilch`` is a small library for recording and viewing exceptions from Python.
This library is inspired by (and uses several of the same functions from)
`David Cramer's Sentry <https://github.com/dcramer/sentry>`_, but aims to
implement just the core features in a smaller code/feature footprint.


Requirements
============

* ``simplejson``
* ``weberror``

Optional
--------

* `zeromq <http://zeromq.org>`_ (For network based reporting)
* `sqlalchemy <http://sqlalchemy.org/>`_ (For the database backend recorder)


Basic Usage
===========

Reporting an Exception
----------------------

In the application that wants to report errors, import zilch and configure
the reporter to record directly to the database::
    
    from zilch.store import SQLAlchemyStore
    import zilch.client
    
    zilch.client.store = SQLAlchemyStore('sqlite:///exceptions.db')


Then to report an exception::
    
    from zilch.client import capture_exception
    try:
        # do something that explodes
    except Exception, e:
        capture_exception()

The error will then be recorded in the database for later viewing.


Advanced Usage
==============

In larger cluster scenarios, or where latency is important, the reporting of
the exception can be handed off to `zeromq <http://zeromq.org>`_ to be
recorded to a central recorder over the network. Both the client and recording
machine must have `zeromq <http://zeromq.org>`_ installed.

To setup the client for recording::

    import zilch.client

    zilch.client.recorder_host = "tcp://localhost:5555"


Then to report an exception::
    
    from zilch.client import capture_exception
    try:
        # do something that explodes
    except Exception, e:
        capture_exception()

The exception will then be sent to the recorder_host listening at the
``recorder_host`` specified.


Recording Exceptions Centrally
==============================

The recorder uses `zeromq <http://zeromq.org>`_ to record exception reports
delivered over the network. To run the recorder host, on the machine recording
them run::

    >> zilch-recorder tcp://localhost:5555 sqlite:///exceptions.db

Without a ``Recorder`` running, ZeroMQ will hold onto the messages until it
is available. After which point, it will begin to block (In the future, an
option will be added to configure the disk offloading of messages).

The recorder will create the tables necessary on its initial launch.


Viewing Recorded Exceptions
===========================

``zilch`` comes with a `pyramid
<http://docs.pylonsproject.org/docs/pyramid.html>`_ web application to view
the database of recorded exceptions. Once you have installed Pyramid, you can
run the web interface by typing::
    
    >> zilch-web sqlite:///exceptions.db

Additional web configuration parameters are available to designate the
host/port that the web application should bind to (viewable by running
``zilch-web`` with the ``-h`` option).


License
=======

``zilch`` is offered under the MIT license.


Authors
=======

``zilch`` is made available by `Ben Bangert`.
