import sys
import time
import logging
import optparse
import socket
import hashlib
from getpass import getpass
from repoze.lru import lru_cache
from pegasus.metrics import db

log = logging.getLogger("pegasus.metrics.loader")

def reprocess_raw_data():
    db.delete_processed_data()
    
    i = 0    
    for data in db.each_raw_data():
        i += 1
        process_raw_data(data)
    
    return i

@lru_cache(1024, timeout=3600)
def get_hostname_domain(ipaddr):
    if ipaddr == "127.0.0.1":
        return "localhost", "localdomain"
    
    try:
        log.debug("Looking up %s" % ipaddr)
        hostname = socket.gethostbyaddr(ipaddr)[0]
        log.debug("%s is %s" % (ipaddr, hostname))
        
        # The domain is everything after the first dot
        # unless there is no dot, then it is everything
        domain = hostname[hostname.find(".")+1:]
        
        return hostname, domain
    except:
        log.warning("No such host: %s" % ipaddr)
        return None, None

def process_raw_data(data):
    try:
        # Get the hostname and domain
        ipaddr = data["remote_addr"]
        hostname, domain = get_hostname_domain(ipaddr)
        data["hostname"] = hostname
        data["domain"] = domain
        
        # Process metrics according to type
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
    except Exception, e:
        log.exception(e)
        db.store_invalid_data(data["id"], unicode(e))

def process_planner_metrics(data):
    
    # Remove the nested structure the planner sends
    metrics = data["wf_metrics"]
    del data["wf_metrics"]
    data.update(metrics)
    
    # Change start_time and end_time into timestamps if they
    # are using the old string formats
    datefmt = "%b %d, %Y %H:%M:%S %p"
    start_time = data["start_time"]
    if isinstance(start_time, basestring):
        if start_time[0] in "0123456789":
            data["start_time"] = float(start_time)
        else:
            log.debug("Using old string format for planner start_time")
            ts = time.mktime(time.strptime(start_time, datefmt))
            data["start_time"] = ts
    
    end_time = data["end_time"]
    if isinstance(end_time, basestring):
        if end_time[0] in "0123456789":
            data["end_time"] = float(end_time)
        else:
            log.debug("Using old string format for planner end_time")
            ts = time.mktime(time.strptime(end_time, datefmt))
            data["end_time"] = ts

    if "data_config" not in data:
        data["data_config"] = None
    
    db.store_planner_metrics(data)

def hash_error(error):
    # XXX We assume it is a Java stacktrace for now
    # When we get more data we can revise our processing
    
    # Each stack trace has several lines
    lines = error.split("\n")
    
    # Line 0 should start with the exception type followed by a colon
    exception = lines[0]
    colon = exception.find(":")
    if colon > 0:
        exception = exception[0:colon]
    else:
        log.warn("Did not find a colon in exception stack trace line 0:\n%s" % lines[0])
        exception = "java.lang.RuntimeException"
    
    # Line 1 should be where the exception was thrown and start with "at"
    location = lines[1]
    if not location.lstrip().startswith("at "):
        log.warn("Exception stack trace line 1 does not look like a location:\n%s" % lines[1])
    
    # Use MD5 to create a hash
    md = hashlib.md5()
    md.update(exception)
    md.update(location)
    errhash = md.hexdigest()
    
    return errhash

def process_planner_error(data):
    objid = data["id"]
    message = data["error"]
    errhash = hash_error(message)
    
    error = {
        "id": objid,
        "error": message,
        "hash": errhash
    }
    
    db.store_planner_errors(error)

def main():
    parser = optparse.OptionParser()
    
    db.add_options(parser)
    
    (opts, args) = parser.parse_args()
    
    if len(args) > 0:
        parser.error("Invalid argument")
    
    if opts.passwd is None:
        opts.passwd = getpass("Database password: ")
    
    try:
        db.connect(host=opts.host,
                   port=opts.port,
                   user=opts.user,
                   passwd=opts.passwd,
                   db=opts.db)
        reprocess_raw_data()
        db.commit()
    except:
        db.rollback()
        raise
    finally:
        db.close()

