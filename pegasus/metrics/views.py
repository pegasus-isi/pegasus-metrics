try:
    import json
except ImportError:
    import simplejson as json
import pprint
import logging
import time
import requests
from flask import request, render_template, redirect, url_for, g, flash, Markup, session

from pegasus.metrics import app, db, ctx, loader, forms

log = logging.getLogger(__name__)

MAX_CONTENT_LENGTH = 16*1024

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

@app.context_processor
def inject_date():
    return dict(current_date=time.time())

@app.route('/')
def index():
    form = forms.PeriodForm(formdata=request.args)
    form.validate()
    start = form.get_start()
    
    raw = db.count_raw_data(start)
    invalid = db.count_invalid_data(start)
    errors = db.count_planner_errors(start)
    stats = db.get_planner_stats(start)
    downloads = db.count_downloads(start)
    
    top_hosts = db.get_top_hosts(5, start)
    top_domains = db.get_top_domains(5, start)
    
    return render_template('index.html',
            raw=raw,
            invalid=invalid,
            planner_errors=errors,
            planner_stats=stats,
            top_hosts=top_hosts,
            top_domains=top_domains,
            downloads=downloads,
            form=form)

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
    form = forms.PeriodForm(request.args)
    form.validate()
    start = form.get_start()
    errors = db.get_top_errors(start)
    return render_template('top_errors.html',
            errors=errors,
            form=form)

@app.route('/planner/topdomains')
def top_domains():
    form = forms.PeriodForm(request.args)
    form.validate()
    start = form.get_start()
    domains = db.get_top_domains(50, start)
    return render_template('top_domains.html',
            domains=domains,
            form=form)

@app.route('/planner/tophosts')
def top_hosts():
    form = forms.PeriodForm(request.args)
    form.validate()
    start = form.get_start()
    hosts = db.get_top_hosts(50, start)
    return render_template('top_hosts.html',
            hosts=hosts,
            form=form)

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

@app.route('/downloads/popular')
def popular_downloads():
    form = forms.PeriodForm(request.args)
    form.validate()
    start = form.get_start()
    dls = db.get_popular_downloads(start)
    return render_template('popular_downloads.html',
            downloads=dls,
            form=form)

def get_location(ipaddr):
    location = None
    if ipaddr:
        try:
            r = requests.get("http://freegeoip.net/json/%s" % ipaddr)
            if 200 <= r.status_code < 300:
                location = json.loads(r.text)
        except:
            pass
    return location

@app.route('/downloads/metrics/<objid>')
def download_metric(objid):
    obj = db.get_download(objid)
    location = get_location(obj["remote_addr"])
    return render_template('download_metric.html',
            obj=obj,
            location=location)

@app.route('/status')
def status():
    # Make sure the database is reachable and that
    # it received some data in the last 24 hours
    
    now = time.time()
    then = now - (24*60*60)
    count = db.count_raw_data(then)
    
    if count == 0:
        return "No data in last 24 hours", 503
    
    return "OK", 200

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
    ts = data["ts"]
    
    # Get the remote IP address. The downloads will have
    # a remote_addr already, so don't add it if the key 
    # exists
    if "remote_addr" not in data:
        data["remote_addr"] = request.environ["REMOTE_ADDR"]
    remote_addr = data["remote_addr"]
    
    # Store the raw data
    try:
        data["id"] = db.store_raw_data(ts, remote_addr, data)
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

