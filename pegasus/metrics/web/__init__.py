from flask import Flask

app = Flask("pegasus.metrics.web")

import pegasus.metrics.web.views

