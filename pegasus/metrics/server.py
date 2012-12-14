try:
    import json
except ImportError:
    import simplejson as json
import logging
from flask import Flask, request, abort

app = Flask("pegasus-metrics")

@app.route('/status')
def status():
    # TODO Perform status checks
    return "", 200

@app.route('/metrics', methods=["POST"])
def store_metrics():
    # Check the content-type
    if request.headers["Content-Type"] != "application/json":
        logging.error("Invalid Content-Type")
        return "Invalid Content-Type", 400
    
    # Parse the request
    try:
        data = json.loads(request.data)
    except Exception, e:
        logging.error("Error parsing JSON object: %s", e)
        return "Error parsing JSON object", 400
    
    # Get the remote IP address
    data["external_address"] = request.environ["REMOTE_ADDR"]
    
    print data
    
    return "", 202

if __name__ == "__main__":
    app.debug = True
    
    app.run()

