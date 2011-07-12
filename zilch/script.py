import sys
from optparse import OptionParser

from zilch.collector import Collector

class ZilchCollector(object):
    def main(self):
        from zilch.stores.sqla import SQLAlchemyStore
        usage = "usage: %prog zeromq_bind database_uri"
        parser = OptionParser(usage=usage)
        (options, args) = parser.parse_args()
        
        if len(args) < 2:
            sys.exit("Error: Failed to provide necessary arguments")
        
        store = SQLAlchemyStore(uri=args[1])
        collector = Collector(zeromq_bind=args[0], store=store)
        collector.main_loop()


def main():
    zilch = ZilchCollector()
    sys.exit(zilch.main())
