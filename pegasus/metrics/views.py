try:
    import json
except ImportError:
    import simplejson as json
import logging
import time
from flask import request, render_template, redirect, url_for, g
import MySQLdb as mysql
from MySQLdb.cursors import DictCursor

from pegasus.metrics import app

log = logging.getLogger(__name__)

MAX_CONTENT_LENGTH = 16*1024

def connect_db():
    return mysql.connect(
        host=app.config["DBHOST"],
        user=app.config["DBUSER"],
        passwd=app.config["DBPASS"],
        db=app.config["DBNAME"],
        cursorclass=DictCursor,
        use_unicode=True)

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    if exception is not None:
        g.db.rollback()
    g.db.close()

def store_json_data(data):
    cur = g.db.cursor()
    try:
        cur.execute("INSERT INTO json_data (data) VALUES (%s)", 
                [json.dumps(data)])
    finally:
        cur.close()

def count_json_data():
    cur = g.db.cursor()
    try:
        cur.execute("SELECT count(*) as count FROM json_data")
        return cur.fetchone()['count']
    finally:
        cur.close()

@app.route('/')
def index():
    nrows = count_json_data()
    return render_template('index.html', nrows=nrows)

@app.route('/status')
def status():
    # Make sure the database is reachable
    count_json_data()
    
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
    
    # Get the remote IP address
    data["remote_addr"] = request.environ["REMOTE_ADDR"]
    data["ts"] = time.time()
    
    # Store the data
    try:
        store_json_data(data)
    except Exception, e:
        log.error("Error storing JSON data: %s", e)
        return "Error storing JSON data", 500
    
    return "", 202

