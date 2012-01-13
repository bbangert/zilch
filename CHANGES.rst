=====
zilch
=====

0.1.3 (01/13/2012)
==================

Features
--------

- Applied pull request from Marius Gedminas to add prefix option support to the
  error view webapp.


0.1.2 (08/07/2011)
==================

Bug Fixes
---------

- Cleanup session at end of request.


0.1.1 (07/25/2011)
==================

Bug Fixes
---------

- Fix bug with webob imports in client.py


0.1 (07/25/2011)
================

Features
--------

- Exception reporting via SQLAlchemy and/or ZeroMQ
- Recording Store can be pluggable
- WSGI Middleware to capture exceptions with WSGI/CGI environment data
- Web User Interface for the recorder to view collected exceptions
- Event tagging to record additional information per exception such as the
  Hostname, Application, etc.
