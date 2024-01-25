import logging
import optparse

from pegasus.metrics import app
from pegasus.metrics import db
from pegasus.metrics import loader

logging.basicConfig(level=app.config["LOGLEVEL"], format=app.config["LOGFORMAT"])

log = logging.getLogger(__name__)

parser = optparse.OptionParser()

parser.add_option("-a", "--all", action="store_true", default=False, dest="all",
        help="Reprocess all raw metrics (default: only reprocess invalid metrics")

(opts, args) = parser.parse_args()

if len(args) > 0:
    parser.error("Invalid argument")

try:
    db.connect()
    if opts.all:
        log.info("Reprocessing raw data")
        records = loader.reprocess_raw_data()
    else:
        log.info("Reprocessing invalid data")
        records = loader.reprocess_invalid_data()
    db.commit()
    log.info("Reloaded %d records", records)
except:
    db.rollback()
    raise
finally:
    db.close()

