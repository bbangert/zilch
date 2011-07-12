=====
zilch
=====

``zilch`` is a small extensible `ZeroMQ <zeromq.org>`_ based reporting and
collecting library for Python. This library is inspired by (and uses several
of the same functions from)`David Cramer's Sentry
<https://github.com/dcramer/sentry>`_, but aims to implement just the core
features in a smaller code/feature footprint with additional functionality
provided purely by additional extension packages.


Requirements
============

* `zeromq <http://zeromq.org>`_
* `sqlalchemy <http://sqlalchemy.org/>`_ for the built-in SQLAlchemy collector
   backend

Usage
=====

Reporting an Exception
----------------------

In the application that wants to report errors, import zilch and configure
the reporter::
    
    import zilch.client
    
    zilch.client.collector_host = "tcp://localhost:5555"

Then to report an exception::
    
    from zilch.client import capture_exception
    try:
        # do something that explodes
    except Exception, e:
        capture_exception()

The exception will then be sent to the collector listening at the
``collector_host`` specified.


Collecting Exceptions
---------------------

Without a ``Collector`` running, ZeroMQ will hold onto the messages until it
is available. After which point, it will begin to block (In the future, an
option will be added to configure the disk offloading of messages).

To start up a Collector, create a database in your SQLAlchemy supported
database, then start the collector and provide the ZeroMQ connection string to
bind the socket to, and the SQLAlchemy database URI::
    
    > zilch-collector tcp://127.0.0.1:5555 postgresql://zilch:zilch@localhost/zilch

The zilch collector will create the tables necessary on its initial launch.

License
=======

``zilch`` is offered under the MIT license.


Authors
=======

``zilch`` is made available by `Ben Bangert`.
