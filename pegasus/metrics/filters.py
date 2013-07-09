import locale
import time
from flask import Markup
from pegasus.metrics import app

locale.setlocale(locale.LC_ALL, "en_US.UTF-8")

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
        return "0"
    if isinstance(num, basestring):
        return num
    return locale.format("%d", num, True)

@app.template_filter('float')
def float_filter(num):
    if num is None:
        return "0.0"
    if isinstance(num, basestring):
        return num
    return locale.format("%0.2f", num, True)

@app.template_filter('timestamp')
def timestamp_filter(ts):
    if ts is None:
        return ""
    if ts == 0:
        return "the beginning of time"
    local = time.localtime(ts)
    return time.strftime("%Y-%m-%d %H:%M:%S", local)

@app.template_filter('simpledate')
def timestamp_filter(ts):
    if ts is None:
        return ""
    if ts == 0:
        return "the beginning of time"
    local = time.localtime(ts)
    return time.strftime("%B %d, %Y", local)

