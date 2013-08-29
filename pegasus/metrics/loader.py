import time
import logging
import optparse
import socket
import hashlib
import re
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

def reprocess_invalid_data():
    ids = db.get_invalid_ids()
    db.delete_invalid_data()

    i = 0
    for data in db.each_raw_data(ids):
        i += 1
        process_raw_data(data)

    return i

@lru_cache(1024, timeout=3600)
def get_hostname_domain(ipaddr):
    if ipaddr is None:
        return None, None

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
        return ipaddr, ipaddr

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
        elif (client, dtype) == ("condor_dagman", "metrics"):
            process_dagman_metrics(data)
        elif dtype == "download":
            process_download(data)
        else:
            error = "Unknown client/data type: %s/%s" % (client, dtype)
            log.warn(error)
            db.store_invalid_data(data["id"], error)
    except Exception, e:
        log.exception(e)
        db.store_invalid_data(data["id"], repr(e))

def process_download(data):
    def nullify(key):
        if not key in data:
            data[key] = None
            return

        if len(data[key].strip()) == 0:
            data[key] = None

    # Convert missing and empty mappings to None
    nullify('name')
    nullify('email')
    nullify('organization')
    nullify('app_domain')
    nullify('app_description')
    nullify('howheard')
    nullify('howhelp')
    nullify('oldfeatures')
    nullify('newfeatures')

    # If the filename has a version string, then extract it
    # Always extract the longest string that looks like a version
    filename = data["filename"]
    ver = None
    for m in re.finditer(r"\d+(\.\d+)+", filename):
        newver = m.group(0)
        if ver is None or len(newver) > len(ver):
            ver = newver
    data["version"] = ver

    db.store_download(data)

def process_planner_metrics(data):
    if "wf_uuid" not in data:
        raise Exception("wf_uuid missing")

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

    if "app_metrics" in data:
        app_metrics = data["app_metrics"]
        if "name" in app_metrics:
            data["application"] = app_metrics["name"]

    if "application" not in data:
        data["application"] = None

    db.store_planner_metrics(data)

def process_dagman_metrics(data):
    if "parent_dagman_id" not in data or len(data["parent_dagman_id"]) == 0:
        data["parent_dagman_id"] = None

    if "planner" not in data or len(data["planner"]) == 0:
        data["planner"] = None

    if "planner_version" not in data or len(data["planner_version"]) == 0:
        data["planner_version"] = None

    if "total_job_time" not in data:
        data["total_job_time"] = None

    db.store_dagman_metrics(data)

def hash_error(error):
    # XXX We assume it is a Java stacktrace for now
    # When we get more data we can revise our processing

    # Use MD5 to create a hash
    md = hashlib.md5()

    # Each stack trace has several lines
    lines = error.split("\n")

    # Line 0 should start with the exception type followed by a colon
    # If there is no colon, then just assume there was no message
    colon = lines[0].find(":")
    if colon > 0:
        md.update(lines[0][0:colon])
    else:
        md.update(lines[0])

    # The line where the exception was thrown should be the first one starting with "at"
    location_found = False
    for l in lines[1:]:
        if l.lstrip().startswith("at "):
            md.update(l)
            location_found = True
            break
    if not location_found:
        log.warn("Stack trace does not appear to have a location:\n%s" % error)

    # If the exception was caused by another, then take that into account
    for i in range(0, len(lines)):
        if lines[i].startswith("Caused by: "):
            cause = lines[i].split(":")[1]
            md.update(cause)
            if i+1 < len(lines):
                md.update(lines[i+1])
            else:
                log.warn("No location for cause in stack trace:\n%s" % error)

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

    parser.add_option("-a", "--all", action="store_true", default=False, dest="all",
            help="Reprocess all raw metrics (default: only reprocess invalid metrics")

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
        if opts.all:
            reprocess_raw_data()
        else:
            reprocess_invalid_data()
        db.commit()
    except:
        db.rollback()
        raise
    finally:
        db.close()

