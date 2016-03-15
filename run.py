import logging

from pegasus.metrics import app

logging.basicConfig(level=app.config["LOGLEVEL"], format=app.config["LOGFORMAT"])

app.run(app.config["HOST"], app.config["PORT"])

