import sys
import cmdln

import zilch

class ZilchCollector(cmdln.Cmdln):
    name = "zilch-collector"

    @cmdln.alias("sqla")
    def do_sqlalchemy(self, subcmd, opts, zeromq_bind, database_uri):
        """${cmd_name}: Run the zilch-collector with the SQLAlchemy backend

        ${cmd_usage}
        ${cmd_option_list}
        
        """
        from zilch.stores.sqla import SQLAlchemyStore
        store = SQLAlchemyStore(uri=database_uri)
        collector = zilch.Collector(zeromq_bind=zeromq_bind, store=store)
        collector.main_loop()


def main():
    zilch = ZilchCollector()
    sys.exit(zilch.main())
