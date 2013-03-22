import sys
import logging
import optparse
from getpass import getpass
from pegasus.metrics import app, db

log = logging.getLogger("pegasus.metrics.server")

def main():
    parser = optparse.OptionParser()
    
    db.add_options(parser)
    
    parser.add_option("-d", "--debug", dest="debug", action="store_true",
            help="Turn on debugging", default=False)
    parser.add_option("-b", "--bind-address", dest="bind_address", action="store",
            help="Specify address to bind to", default="127.0.0.1") 
    parser.add_option("-l", "--listen-port", dest="listen_port", action="store",
            help="Port to listen on", default=5000, type="int")

    (opts, args) = parser.parse_args()
    
    if len(args) > 0:
        parser.error("Invalid argument")
    
    if opts.passwd is None:
        opts.passwd = getpass("Database password: ")
    
    app.config["DBHOST"] = opts.host
    app.config["DBPORT"] = opts.port
    app.config["DBUSER"] = opts.user
    app.config["DBPASS"] = opts.passwd
    app.config["DBNAME"] = opts.db
    app.config["DEBUG"] = opts.debug
    
    if opts.debug:
        # This is required because the reloader will rerun
        # this script, which causes it to ask for the password
        # again, which gets really annoying when you are in
        # development mode
        sys.argv += ["-p", opts.passwd]
        
        # Set the root logging level to debug
        root = logging.getLogger("pegasus.metrics")
        root.setLevel(logging.DEBUG)
    
    app.run(opts.bind_address, opts.listen_port)

