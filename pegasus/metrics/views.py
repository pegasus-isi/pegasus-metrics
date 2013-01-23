try:
    import json
except ImportError:
    import simplejson as json
import pprint
import logging
import time
import locale
import datetime
from flask import request, render_template, redirect, url_for, g, flash, Markup

from pegasus.metrics import app, db, ctx, loader

log = logging.getLogger(__name__)

MAX_CONTENT_LENGTH = 16*1024

locale.setlocale(locale.LC_ALL, "en_US.UTF-8")

@app.before_request
def before_request():
    db.connect(host=app.config["DBHOST"],
               port=app.config["DBPORT"],
               user=app.config["DBUSER"],
               passwd=app.config["DBPASS"],
               db=app.config["DBNAME"])

@app.teardown_request
def teardown_request(exception):
    if exception is not None:
        db.rollback()
    db.close()

@app.template_filter('null')
def null_filter(obj):
    if obj is None:
        return Markup('<span class="na">n/a</span>')
    else:
        return obj

@app.template_filter('yesno')
def yesno_filter(boolean):
    if boolean:
        return "Yes"
    else:
        return "No"

@app.template_filter('decimal')
def decimal_filter(num):
    if num is None:
        return ""
    if isinstance(num, basestring):
        return num
    return locale.format("%d", num, True)

@app.template_filter('timestamp')
def timestamp_filter(ts):
    if ts is None:
        return ""
    local = time.localtime(ts)
    return time.strftime("%Y-%m-%d %H:%M:%S", local)

@app.route('/')
def index():
    raw = db.count_raw_data()
    invalid = db.count_invalid_data()
    errors = db.count_planner_errors()
    stats = db.get_planner_stats()
    downloads = db.count_downloads()
    
    top_hosts = db.get_top_hosts(5)
    top_domains = db.get_top_domains(5)
    
    return render_template('index.html',
            raw=raw,
            invalid=invalid,
            planner_errors=errors,
            planner_stats=stats,
            top_hosts=top_hosts,
            top_domains=top_domains,
            downloads=downloads)

@app.route('/reprocess', methods=["POST"])
def reprocess():
    i = loader.reprocess_raw_data()
    db.commit()
    flash("Reprocessed %d objects successfully" % i)
    return redirect(request.referrer or url_for('index'))

@app.route('/invalid')
def invalid():
    objects = db.get_invalid_data()
    for obj in objects:
        data = obj["data"]
        data = json.loads(data)
        obj["data"] = json.dumps(data, indent=4)
    return render_template('invalid.html',
            objects=objects)

@app.route('/planner/recenterrors')
def recent_errors():
    errors = db.get_recent_errors()
    return render_template('recent_errors.html',
            errors=errors)

@app.route('/planner/toperrors')
def top_errors():
    errors = db.get_top_errors()
    return render_template('top_errors.html',
            errors=errors)

@app.route('/planner/topdomains')
def top_domains():
    domains = db.get_top_domains(50)
    return render_template('top_domains.html',
            domains=domains)

@app.route('/planner/tophosts')
def top_hosts():
    hosts = db.get_top_hosts(50)
    return render_template('top_hosts.html',
            hosts=hosts)

@app.route('/planner/errorsbyhash/<errhash>')
def error_hash(errhash):
    title = "Errors with hash %s" % errhash
    errors = db.get_errors_by_hash(errhash)
    return render_template('error_list.html',
            title=title,
            errors=errors)

@app.route('/planner/metrics/<objid>')
def planner_metric(objid):
    obj = db.get_metrics_and_error(objid)
    return render_template('planner_metric.html',
            obj=obj)

@app.route('/downloads/recent')
def recent_downloads():
    dls = db.get_recent_downloads(50)
    return render_template('recent_downloads.html',
            downloads=dls)

@app.route('/downloads/metrics/<objid>')
def download_metric(objid):
    obj = db.get_download(objid)
    return render_template('download_metric.html',
            obj=obj)

@app.route('/status')
def status():
    # Make sure the database is reachable
    db.count_raw_data()
    
    # TODO Perform other status checks
    
    return "", 200

@app.route('/metrics', methods=["POST"])
def store_metrics():
    # Check the content-type
    try:
        type_header = request.headers["Content-Type"]
        if type_header.lower() != "application/json":
            log.error("Invalid Content-Type")
            return "Invalid Content-Type", 400
    except:
        return "Invalid Content-Type", 400
    
    # Check the length
    try:
        length = int(request.headers["Content-Length"])
        if length > MAX_CONTENT_LENGTH:
            return "Request too large", 400
    except:
        return "Invalid Content-Length", 400
    
    # Read and parse the data
    try:
        raw = request.stream.read(length)
        if not request.stream.is_exhausted:
            return "Invalid Content-Length", 400
        data = json.loads(raw)
    except Exception, e:
        log.error("Error parsing JSON object: %s", e)
        return "Error parsing JSON object", 400
    
    # TODO Validate required fields
    if "type" not in data:
        return "type missing", 400
    if "client" not in data:
        return "client missing", 400
    if "version" not in data:
        return "version missing", 400
    
    # Record the time that the data was received
    # The old downloads will have a timestamp already, so
    # don't add one if the key exists
    if "ts" not in data:
        data["ts"] = time.time()
    
    # Get the remote IP address. The downloads will have
    # a remote_addr already, so don't add it if the key 
    # exists
    if "remote_addr" not in data:
        data["remote_addr"] = request.environ["REMOTE_ADDR"]
    
    # Store the raw data
    try:
        data["id"] = db.store_raw_data(data)
        db.commit()
    except Exception, e:
        log.error("Error storing JSON data: %s", e)
        db.rollback()
        return "Error storing JSON data", 500
    
    # Store the processed data
    try:
        loader.process_raw_data(data)
        db.commit()
    except Exception, e:
        log.error("Error processing JSON data: %s", e)
        db.rollback()
    
    return "", 202

