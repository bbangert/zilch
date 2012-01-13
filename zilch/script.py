import sys
from optparse import OptionParser

from paste.httpserver import serve

from zilch.recorder import Recorder

class ZilchRecorder(object):
    def main(self):
        from zilch.store import SQLAlchemyStore
        usage = "usage: %prog zeromq_bind database_uri"
        parser = OptionParser(usage=usage)
        (options, args) = parser.parse_args()
        
        if len(args) < 2:
            sys.exit("Error: Failed to provide necessary arguments")
        
        store = SQLAlchemyStore(uri=args[1])
        recorder = Recorder(zeromq_bind=args[0], store=store)
        recorder.main_loop()


class ZilchWeb(object):
    def main(self):
        from zilch.web import make_webapp
        usage = "usage: %prog database_uri"
        parser = OptionParser(usage=usage)
        parser.add_option("--port", dest="port", type="int", default=8000,
                          help="Port to bind the webserver to")
        parser.add_option("--host", dest="hostname", default="127.0.0.1",
                          help="Hostname/IP to bind the webserver to")
        parser.add_option("--timezone", dest="timezone", default="US/Pacific",
                          help="Default timezone to format dates for")                          
        parser.add_option("--prefix", dest="prefix",
                          help="URL prefix")
        (options, args) = parser.parse_args()
        
        if len(args) < 1:
            sys.exit("Error: Failed to provide a database_uri")
        
        app = make_webapp(args[0], default_timezone=options.timezone)
        if options.prefix:
            from paste.deploy.config import PrefixMiddleware
            app = PrefixMiddleware(app, prefix=options.prefix)
        return serve(app, host=options.hostname, port=options.port)


def zilch_recorder():
    zilch = ZilchRecorder()
    sys.exit(zilch.main())

def zilch_web():
    try:
        import pyramid
    except ImportError:
        raise SystemExit("Pyramid 1.0 or greater must be installed before running zilch-web.")
    web = ZilchWeb()
    sys.exit(web.main())
