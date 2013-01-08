try:
    import json
except ImportError:
    import simplejson as json
import pprint
import logging
import time
import locale
from flask import request, render_template, redirect, url_for, g, flash

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

@app.template_filter('decimal')
def decimal_filter(num):
    if isinstance(num, basestring):
        return num
    return locale.format("%d", num, True)

@app.route('/')
def index():
    raw = db.count_raw_data()
    invalid = db.count_invalid_data()
    errors = db.count_planner_errors()
    stats = db.get_planner_stats()

    top_hosts = db.get_top_hosts()
    top_domains = db.get_top_domains()
    
    return render_template('index.html',
            raw=raw,
            invalid=invalid,
            planner_errors=errors,
            planner_stats=stats,
            top_hosts=top_hosts,
            top_domains=top_domains)

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

@app.route('/errors')
def errors():
    errors = db.get_planner_errors()
    return render_template('errors.html',
            errors=errors)

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
    if "wf_uuid" not in data:
        return "wf_uuid missing", 400
    if "type" not in data:
        return "type missing", 400
    if "client" not in data:
        return "client missing", 400
    if "version" not in data:
        return "version missing", 400
    
    # Get the remote IP address
    data["remote_addr"] = request.environ["REMOTE_ADDR"]
    data["ts"] = time.time()
    
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

