try:
    import json
except ImportError:
    import simplejson as json
import logging
import time
import requests
from flask import request, render_template, redirect, url_for, flash, session

from pegasus.metrics import app, db, loader, forms

log = logging.getLogger(__name__)

MAX_CONTENT_LENGTH = 16*1024

@app.before_request
def before_request():
    db.connect()

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
    if request.args or 'formdata' not in session:
        session['formdata'] = request.args
    form = forms.PeriodForm(formdata=session['formdata'])
    form.validate()
    start = form.get_start()
    end = form.get_end()


    raw = db.count_raw_data(start, end)
    invalid = db.count_invalid_data(start, end)
    errors = db.count_planner_errors(start, end)
    planner_stats = db.get_planner_stats(start, end)
    dagman_stats = db.get_dagman_stats(start, end)
    downloads = db.count_downloads(start, end)

    table_args = {
        "limit" : 5,
        "offset" : 0,
        "start_time" : start,
        "end_time" : end
    }
    # These count variables are just dummies to get the top_hosts and top_domains
    totalCount, filterCount, top_hosts = db.get_top_hosts(**table_args)
    totalCount, filterCount, top_domains = db.get_top_domains(**table_args)


    return render_template('index.html',
            raw=raw,
            invalid=invalid,
            planner_errors=errors,
            planner_stats=planner_stats,
            dagman_stats=dagman_stats,
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
    if request.is_xhr:
        table_args = __get_datatables_args()
        totalCount, filteredCount, errors = db.get_recent_errors(**table_args)
        return render_template('recent_errors.json', table_args=table_args, count=totalCount, filtered=filteredCount, errors=errors)

    if request.args or 'formdata' not in session:
        session['formdata'] = request.args
    form = forms.PeriodForm(formdata=session['formdata'])
    form.validate()
    return render_template('recent_errors.html', form=form)

@app.route('/planner/toperrors')
def top_errors():
    if request.is_xhr:
        table_args = __get_datatables_args()
        totalCount, filteredCount, errors = db.get_top_errors(**table_args)
        return render_template('top_errors.json', table_args=table_args, count=totalCount, filtered=filteredCount, errors=errors)

    if request.args or 'formdata' not in session:
        session['formdata'] = request.args
    form = forms.PeriodForm(formdata=session['formdata'])
    form.validate()
    return render_template('top_errors.html', form=form)

@app.route('/planner/topdomains')
def top_domains():
    if request.is_xhr :
        table_args = __get_datatables_args()
        totalCount, filteredCount, domains = db.get_top_domains(**table_args)
        return render_template('top_domains.json', table_args=table_args, count=totalCount, filtered=filteredCount, domains=domains)

    if request.args or 'formdata' not in session:
        session['formdata'] = request.args
    form = forms.PeriodForm(formdata=session['formdata'])
    form.validate()
    return render_template('top_domains.html', form=form)

@app.route('/planner/tophosts')
def top_hosts():
    if request.is_xhr:
        table_args = __get_datatables_args()
        totalCount, filteredCount, hosts = db.get_top_hosts(**table_args)
        return render_template('top_hosts.json', table_args=table_args, count=totalCount, filtered=filteredCount, hosts=hosts)

    if request.args or 'formdata' not in session:
        session['formdata'] = request.args
    form = forms.PeriodForm(formdata=session['formdata'])
    form.validate()
    return render_template('top_hosts.html', form=form)

@app.route('/planner/errorsbyhash/<errhash>')
def error_hash(errhash):
    if request.is_xhr:
        table_args = __get_datatables_args()
        totalCount, filteredCount, errors = db.get_errors_by_hash(**table_args)
        return render_template('error_list.json', table_args=table_args, count=totalCount, filtered=filteredCount, errors=errors)

    return render_template('error_list.html', err_hash=errhash)

@app.route('/planner/metrics/<objid>')
def planner_metric(objid):
    obj = db.get_metrics_and_error(objid)
    runs = db.get_runs_for_workflow(obj['root_wf_uuid'])
    return render_template('planner_metric.html',
            obj=obj,
            runs=runs)

@app.route('/planner/recentapplications')
def recent_applications():
    if request.is_xhr:
        table_args = __get_datatables_args()
        totalCount, filteredCount, applications = db.get_recent_applications(**table_args)
        return render_template('recent_applications.json', table_args=table_args, count=totalCount, filtered=filteredCount, applications=applications)

    form = forms.PeriodForm(request.args)
    form.validate()
    return render_template('recent_applications.html', form=form)

@app.route('/planner/topapplications')
def top_applications():
    if request.is_xhr:
        table_args = __get_datatables_args()
        totalCount, filteredCount, applications = db.get_top_applications(**table_args)
        return render_template('top_applications.json', table_args=table_args, count=totalCount, filtered=filteredCount, applications=applications)

    if request.args or 'formdata' not in session:
        session['formdata'] = request.args
    form = forms.PeriodForm(formdata=session['formdata'])
    form.validate()
    return render_template('top_applications.html', form=form)

@app.route('/planner/map')
def map_metrics():
    if request.args or 'formdata' not in session:
        session['formdata'] = request.args
    form = forms.MapForm(formdata=session['formdata'])
    form.validate()
    start = form.get_start()
    end = form.get_end()
    pins = form.get_pins()
    locations = db.get_locations(pins, start, end)
    return render_template('maps.html',
                           form =form,
                           locations=locations)
@app.route('/planner/trends')
def planner_trends():
    if request.args or 'formdata' not in session:
        session['formdata'] = request.args
    form = forms.TrendForm(formdata=session['formdata'])
    form.validate()
    intervals = form.get_monthly_intervals()
    trend = []
    for i in range(len(intervals)-1):
        newPlans = db.get_metrics_by_version(intervals[i+1], intervals[i])
        trend.append(newPlans)
    return render_template('planner_trends.html',
                           form=form,
                           intervals=intervals,
                           trend=trend)

@app.route('/planner/histograms')
def histograms():
    if request.args or 'formdata' not in session:
        session['formdata'] = request.args
    form = forms.HistogramForm(formdata=session['formdata'])
    form.validate()
    field = form.get_metric()
    start = form.get_start()
    end = form.get_end()
    intervals = form.get_intervals()
    data = []
    for i in range(1, len(intervals)):
        data.append(db.get_workflow_count_by_field(field, intervals[i-1], intervals[i], start, end))
    return render_template('histograms.html',
                           form=form,
                           trend=data,
                           intervals=intervals)

@app.route('/locations/<ipaddr>')
def location_metric(ipaddr):
    location = db.get_location(ipaddr)
    return render_template('location.html', location=location)

@app.route('/runs/topapplications')
def top_application_runs():
    if request.is_xhr:
        table_args = __get_datatables_args()
        totalCount, filteredCount, applications = db.get_top_application_runs(**table_args)
        return render_template('top_application_runs.json', table_args=table_args, count=totalCount, filtered=filteredCount, applications=applications)

    if request.args or 'formdata' not in session:
        session['formdata'] = request.args
    form = forms.PeriodForm(formdata=session['formdata'])
    form.validate()
    return render_template('top_application_runs.html', form=form)

@app.route('/downloads/recent')
def recent_downloads():
    if request.is_xhr:
        table_args = __get_datatables_args()
        totalCount, filteredCount, downloads = db.get_recent_downloads(**table_args)
        return render_template('recent_downloads.json', table_args=table_args, count=totalCount, filtered=filteredCount, downloads=downloads)

    if request.args or 'formdata' not in session:
        session['formdata'] = request.args
    form = forms.PeriodForm(formdata=session['formdata'])
    form.validate()
    return render_template('recent_downloads.html', form=form)

@app.route('/downloads/popular')
def popular_downloads():
    if request.is_xhr:
        table_args = __get_datatables_args()
        totalCount, filteredCount, downloads = db.get_popular_downloads(**table_args)
        return render_template('popular_downloads.json', table_args=table_args, count=totalCount, filtered=filteredCount, downloads=downloads)

    if request.args or 'formdata' not in session:
        session['formdata'] = request.args
    form = forms.PeriodForm(formdata=session['formdata'])
    return render_template('popular_downloads.html', form=form)

@app.route('/downloads/trends')
def download_trends():
    if request.args or 'formdata' not in session:
        session['formdata'] = request.args
    form = forms.TrendForm(formdata=session['formdata'])
    form.validate()
    intervals = form.get_monthly_intervals()

    trend = []
    for i in range(len(intervals)-1):
        newDownloads = db.get_downloads_by_version(intervals[i+1], intervals[i])
        trend.append(newDownloads)
    return render_template('download_trends.html',
                           form=form,
                           intervals=intervals,
                           trend=trend)

@app.route('/downloads/metrics/<objid>')
def download_metric(objid):
    obj = db.get_download(objid)
    return render_template('download_metric.html', obj=obj)

@app.route('/status')
def status():
    # Make sure the database is reachable and that
    # it received some data in the last 24 hours
    
    now = time.time()
    then = now - (24*60*60)
    count = db.count_raw_data(then, now)
    
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


def __get_datatables_args():
    '''
    Extract list of arguments passed in the request
    '''
    table_args = dict()
    if request.args.get('sEcho'):
        table_args['sequence'] = request.args.get('sEcho')

    if request.args.get('iColumns'):
        table_args['column-count'] = int(request.args.get('iColumns'))

    if request.args.get('sColumns'):
        table_args['columns'] = request.args.get('sColumns')

    if request.args.get('iDisplayStart'):
        table_args['offset'] = int(request.args.get('iDisplayStart'))

    if request.args.get('iDisplayLength'):
        table_args['limit'] = int(request.args.get('iDisplayLength'))

    if request.args.get('sSearch'):
        table_args['filter'] = request.args.get('sSearch')

    if request.args.get('bRegex'):
        table_args['filter-regex'] = request.args.get('bRegex')

    if request.args.get('iSortingCols'):
        table_args['sort-col-count'] = int(request.args.get('iSortingCols'))

    if request.args.get('start_time'):
        table_args['start_time'] = request.args.get('start_time')

    if request.args.get('end_time'):
        table_args['end_time'] = request.args.get('end_time')

    if request.args.get('form_only'):
        table_args['form_only'] = request.args.get('form_only')

    if request.args.get('errhash'):
        table_args['errhash'] = request.args.get('errhash')

    if request.args.get('iColumns'):
        for i in range(int(request.args.get('iColumns'))):
            i = str(i)

            if request.args.get('mDataProp_' + i):
                table_args['mDataProp_' + i] = request.args.get('mDataProp_' + i)

            if request.args.get('sSearch_' + i):
                table_args['sSearch_' + i] = request.args.get('sSearch_' + i)

            if request.args.get('bRegex_' + i):
                table_args['bRegex_' + i] = request.args.get('bRegex_' + i)

            if request.args.get('bSearchable_' + i):
                table_args['bSearchable_' + i] = request.args.get('bSearchable_' + i)

            if request.args.get('iSortCol_' + i):
                table_args['iSortCol_' + i] = int(request.args.get('iSortCol_' + i))

            if request.args.get('bSortable_' + i):
                table_args['bSortable_' + i] = request.args.get('bSortable_' + i)

            if request.args.get('sSortDir_' + i):
                table_args['sSortDir_' + i] = request.args.get('sSortDir_' + i)

    return table_args
