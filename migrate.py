import sys
import logging
import importlib

from pegasus.metrics import app
from pegasus.metrics import db

logging.basicConfig(level=app.config["LOGLEVEL"], format=app.config["LOGFORMAT"])

if len(sys.argv) != 2:
    print "Usage: %s MIGRATION_MODULE" % sys.argv[0]
    print "ex: %s pegasus/metrics/migrations/001_convert_downloads.py" % sys.argv[0]
    exit(1)

modname = sys.argv[1]
modname = modname.replace(".py", "")
modname = modname.replace("/",".")

mod = importlib.import_module(modname)

db.connect()
try:
    mod.migrate()
finally:
    db.close()

