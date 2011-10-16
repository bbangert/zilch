=====
zilch
=====

``zilch`` is a small library for recording and viewing exceptions from Python.
This library is inspired by (and uses several of the same functions from)
David Cramer's Sentry_, but aims to implement just the core features in a
smaller code/feature footprint.


Requirements
============

* simplejson_
* WebError_

Optional
--------

* ZeroMQ_ (For network based reporting)
* SQLAlchemy_ (For the database backend recorder)
* Pyramid_ and WebHelpers_ (For the recorder web UI)


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
the exception can be handed off to ZeroMQ_ to be recorded to a central
recorder over the network. Both the client and recording machine must have
ZeroMQ_ installed.

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

The recorder uses ZeroMQ_ to record exception reports delivered over the
network. To run the recorder host, on the machine recording them run::

    >> zilch-recorder tcp://localhost:5555 sqlite:///exceptions.db

Without a ``Recorder`` running, ZeroMQ_ will hold onto the messages until it
is available. After which point, it will begin to block (In the future, an
option will be added to configure the disk offloading of messages).

The recorder will create the tables necessary on its initial launch.


Viewing Recorded Exceptions
===========================

``zilch`` comes with a Pyramid_ web application to view the database of
recorded exceptions. Once you have installed Pyramid_ and WebHelpers_, you can
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


Support
=======

zilch is considered feature-complete as the project owner (Ben Bangert) has
no additional functionality or development beyond bug fixes planned. Bugs can
be filed on github, should be accompanied by a test case to retain current
code coverage, and should be in a Pull request when ready to be accepted into
the zilch code-base.

For a more full-featured error collector, Sentry_ now has a stand-alone client
that no longer requires Django called Raven_. ``zilch`` was created before
Raven_ was available, and the author now uses Raven_ rather than ``zilch``
most of the time.


.. _Raven: https://github.com/dcramer/raven
.. _Pyramid: http://docs.pylonsproject.org/docs/pyramid.html
.. _ZeroMQ: http://zeromq.org
.. _Sentry: https://github.com/dcramer/sentry
.. _simplejson: http://simplejson.github.com/simplejson/
.. _WebError: http://pypi.python.org/pypi/WebError
.. _SQLAlchemy: http://sqlalchemy.org
.. _WebHelpers: http://sluggo.scrapping.cc/python/WebHelpers/index.html
