try:
    import json
except ImportError:
    import simplejson as json
import logging
import time
from flask import request, render_template, redirect, url_for

from pegasus.metrics import app

MAX_CONTENT_LENGTH = 10*1024

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/status')
def status():
    # TODO Perform status checks
    return "", 200

@app.route('/metrics', methods=["POST"])
def store_metrics():
    # Check the content-type
    try:
        type_header = request.headers["Content-Type"]
        if type_header.lower() != "application/json":
            logging.error("Invalid Content-Type")
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
        logging.error("Error parsing JSON object: %s", e)
        return "Error parsing JSON object", 400
    
    # Get the remote IP address
    data["external_address"] = request.environ["REMOTE_ADDR"]
    data["timestamp"] = time.time()
    
    # TODO Store the data
    #json.dump(data, sys.stderr)
    
    return "", 202

