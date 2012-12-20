import sys
import time
import logging
import optparse
from pegasus.metrics import db

log = logging.getLogger("pegasus.metrics.loader")

def reprocess_raw_data():
    for data in db.each_raw_data():
        try:
            process_raw_data(data)
        except Exception, e:
            log.exception(e)
            db.store_invalid_data(data["id"], unicode(e))

def process_raw_data(data):
    client = data["client"]
    dtype = data["type"]
    if (client, dtype) == ("pegasus-plan", "metrics"):
        process_planner_metrics(data)
    elif (client, dtype) == ("pegasus-plan", "error"):
        process_planner_error(data)
        # Planner errors also contain planner metrics
        process_planner_metrics(data)
    else:
        error = "Unknown client/data type: %s/%s" % (client, dtype)
        log.warn(error)
        db.store_invalid_data(data["id"], error)

def process_planner_metrics(data):
    # Remove the nested structure the planner sends
    metrics = data["wf_metrics"]
    del data["wf_metrics"]
    data.update(metrics)
    
    # Change start_time and end_time into timestamps if they
    # are using the old string format
    datefmt = "%b %d, %Y %H:%M:%S %p"
    start_time = data["start_time"]
    if isinstance(start_time, basestring):
        log.debug("Using old string format for planner start_time")
        ts = time.mktime(time.strptime(start_time, datefmt))
        data["start_time"] = ts
    
    end_time = data["end_time"]
    if isinstance(end_time, basestring):
        log.debug("Using old string format for planner end_time")
        ts = time.mktime(time.strptime(end_time, datefmt))
        data["end_time"] = ts
    
    db.store_planner_metrics(data)

def process_planner_error(data):
    error = {
        "id": data["id"],
        "error": data["error"]
    }
    db.store_planner_errors(error)

def main():
    parser = optparse.OptionParser()
    
    db.add_options(parser)
    
    (opts, args) = parser.parse_args()
    
    if len(args) > 0:
        parser.error("Invalid argument")
    
    try:
        db.connect(host=opts.host,
                   port=opts.port,
                   user=opts.user,
                   passwd=opts.passwd,
                   db=opts.db)
        db.delete_processed_data()
        reprocess_raw_data()
        db.commit()
    except:
        db.rollback()
        raise
    finally:
        db.close()

