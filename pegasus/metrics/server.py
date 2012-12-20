import logging
import optparse
from pegasus.metrics import app, db

log = logging.getLogger("pegasus.metrics.server")

def main():
    parser = optparse.OptionParser()
    
    db.add_options(parser)
    
    parser.add_option("-d", "--debug", dest="debug", action="store_true",
            help="Turn on debugging", default=False)
    
    (opts, args) = parser.parse_args()
    
    if len(args) > 0:
        parser.error("Invalid argument")
    
    app.config["DBHOST"] = opts.host
    app.config["DBPORT"] = opts.port
    app.config["DBUSER"] = opts.user
    app.config["DBPASS"] = opts.passwd
    app.config["DBNAME"] = opts.db
    app.config["DEBUG"] = opts.debug
    
    if opts.debug:
        root = logging.getLogger("pegasus.metrics")
        root.setLevel(logging.DEBUG)
    
    log.info("Starting server...")
    app.run()

