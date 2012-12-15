from flask import Flask

app = Flask("pegasus.metrics")

import pegasus.metrics.views

