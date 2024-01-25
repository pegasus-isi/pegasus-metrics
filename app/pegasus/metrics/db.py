import time

try:
    import json
except ImportError:
    import simplejson as json
import MySQLdb as mysql
from MySQLdb.cursors import DictCursor
import warnings
import threading

from pegasus.metrics import app

# This is a thread local for storing the database connection. We use this
# instead of flask.g because flask.g does not work outside a flask request
# and we need this to work for database migrations, reloading of data, and
# unit tests.
ctx = threading.local()

class WithCursor(DictCursor):
    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

def connect():
    if hasattr(ctx, "db"):
        return
    warnings.filterwarnings('error', category=mysql.Warning)
    ctx.db = mysql.connect(host=app.config["DBHOST"],
                           port=app.config["DBPORT"],
                           user=app.config["DBUSER"],
                           passwd=app.config["DBPASS"],
                           db=app.config["DBNAME"],
                           cursorclass=WithCursor,
                           use_unicode=True)

def commit():
    if hasattr(ctx, "db"):
        ctx.db.commit()

def rollback():
    if hasattr(ctx, "db"):
        ctx.db.rollback()

def close():
    if hasattr(ctx, "db"):
        ctx.db.close()
        del ctx.db

def cursor():
    return ctx.db.cursor()

def store_raw_data(ts, remote_addr, data):
    with cursor() as cur:
        cur.execute("INSERT INTO raw_data (ts, remote_addr, data) VALUES (%s, %s, %s)",
                [ts, remote_addr, json.dumps(data)])

    return ctx.db.insert_id()

def count_raw_data(start=0, end=0):
    with cursor() as cur:
        cur.execute("SELECT count(*) as count FROM raw_data WHERE ts>=%s AND ts <= %s", [start, end])
        return cur.fetchone()['count']

def each_raw_data(ids=None):
    with cursor() as cur:
        query = "SELECT id, ts, remote_addr, data FROM raw_data"
        if ids:
            query += " WHERE id in %s"
            cur.execute(query, [ids])
        else:
            cur.execute(query)
        for row in cur:
            if row is None:
                break
            strdata = row["data"]
            jsondata = json.loads(strdata)
            jsondata["id"] = row["id"]
            jsondata["ts"] = row["ts"]
            jsondata["remote_addr"] = row["remote_addr"]
            yield jsondata

def get_planner_errors():
    with cursor() as cur:
        cur.execute("SELECT * FROM planner_errors")
        return cur.fetchall()

def count_planner_errors(start=0, end=0):
    with cursor() as cur:
        cur.execute("SELECT count(*) as count FROM planner_errors e LEFT JOIN planner_metrics m ON e.id=m.id WHERE m.ts>=%s AND m.ts <= %s", [start, end])
        return cur.fetchone()["count"]

def get_planner_stats(start=0, end=0):
    with cursor() as cur:
        cur.execute("SELECT count(*) as plans, sum(total_tasks) as tasks, sum(total_jobs) as jobs FROM planner_metrics WHERE ts>=%s AND ts <= %s", [start, end])
        return cur.fetchone()

def get_dagman_stats(start=0, end=0):
    with cursor() as cur:
        cur.execute("SELECT count(*) as runs, sum(total_jobs) as total_jobs, sum(total_jobs_run) as jobs_run, sum(jobs_failed+dag_jobs_failed) failed, sum(jobs_succeeded+dag_jobs_succeeded) as succeeded, sum(total_job_time)/3600.0 as total_runtime FROM dagman_metrics WHERE ts>=%s AND ts <= %s", [start, end])
        return cur.fetchone()

def delete_invalid_data():
    with cursor() as cur:
        cur.execute("DELETE FROM invalid_data")

def delete_processed_data():
    with cursor() as cur:
        cur.execute("DELETE FROM invalid_data")
        cur.execute("DELETE FROM planner_metrics")
        cur.execute("DELETE FROM planner_errors")
        cur.execute("DELETE FROM downloads")
        cur.execute("DELETE FROM dagman_metrics")
        cur.execute("DELETE FROM locations")

def get_invalid_ids():
    with cursor() as cur:
        cur.execute("SELECT id FROM invalid_data")
        return [row["id"] for row in cur]

def get_invalid_data():
    with cursor() as cur:
        cur.execute("SELECT i.error, d.data FROM invalid_data i LEFT JOIN raw_data d ON i.id=d.id")
        return cur.fetchall()

def count_invalid_data(start=0, end=0):
    with cursor() as cur:
        cur.execute("SELECT count(*) as count FROM invalid_data i LEFT JOIN raw_data d on i.id=d.id WHERE d.ts>=%s AND d.ts <= %s", [start, end])
        return cur.fetchone()["count"]

def store_invalid_data(id, error=None):
    with cursor() as cur:
        cur.execute("INSERT INTO invalid_data (id, error) VALUES (%s, %s)", [id, error])

def get_top_hosts(**table_args):
    columns = [(True, "hostname"), (False, "workflows"), (False, "tasks"), (False, "jobs")]
    queryClause = "select hostname, count(*) workflows, sum(total_tasks) tasks, sum(total_jobs) jobs, remote_addr from planner_metrics where "
    groupByClause = " group by hostname "
    orderByClause = " order by workflows desc "
    return queryBuilder(queryClause, groupByClause, orderByClause, *columns, **table_args)

def get_top_domains(**table_args):
    columns = [(True, "domain"), (False, "workflows"), (False, "tasks"), (False, "jobs")]
    queryClause = "select domain, hostname, count(*) workflows, sum(total_tasks) tasks, sum(total_jobs) jobs from planner_metrics where "
    groupByClause = " group by domain "
    orderByClause = " order by workflows desc "
    return queryBuilder(queryClause, groupByClause, orderByClause, *columns, **table_args)

def get_top_errors(**table_args):
    columns = [(False, "count"), (True, "error")]
    queryClause = "select hash, count(*) count, max(error) error from planner_errors e left join planner_metrics m on e.id=m.id where "
    groupByClause = " group by hash "
    orderByClause = " order by count desc "
    return queryBuilder(queryClause, groupByClause, orderByClause, *columns, **table_args)

def get_top_applications(**table_args):
    columns = [(True, "application"), (False, "workflows"), (False, "tasks"), (False,"jobs")]
    queryClause = "select application, count(*) workflows, sum(total_tasks) tasks, sum(total_jobs) jobs from planner_metrics where "
    groupByClause = " group by application "
    orderByClause = " order by workflows desc "
    return queryBuilder(queryClause, groupByClause, orderByClause, *columns, **table_args)

def get_errors_by_hash(**table_args):
    """
     This method does not use the query builder function because the page it corresponds with does not specify
     a start or end time, which is assumed for the query builder (it should be possible to slightly modify that function to fix this)
    :param table_args: Arguments passed down from the web page
    :return: The total number of results found, the number of results based on the search criteria, a list of the results
    """
    with cursor() as cur:
        columns = ["id", "error"]

        countClauseStart = "select count(err.id) from ("
        countClauseEnd = ") as err"
        queryClause = "select e.id, e.error from planner_errors e where hash = '%s' " % (table_args["errhash"])
        filterClause = ""
        orderClause = " order by id desc "
        limitClause = ""


        if "filter" in table_args:
            filterValue = "%" + table_args["filter"] + "%"
            filterClause = filterClause + (" and e.error like '%s' " % (filterValue))

        if "iSortCol_0" in table_args:
            orderClause = " order by %s " % (columns[table_args['iSortCol_0']])
            if table_args["sSortDir_0"] == "desc":
                orderClause = orderClause + " desc "

        if "limit" in table_args:
            limitClause = " limit %s offset %s " % (table_args["limit"], table_args["offset"])

        cur.execute(countClauseStart + queryClause + orderClause + countClauseEnd)
        totalCount = cur.fetchone()["count(err.id)"]

        cur.execute(countClauseStart + queryClause + filterClause + orderClause + countClauseEnd)
        filteredCount = cur.fetchone()["count(err.id)"]

        cur.execute(queryClause + filterClause + orderClause + limitClause)
        results = cur.fetchall()
        return totalCount, filteredCount, results

def get_metrics_and_error(objid):
    with cursor() as cur:
        cur.execute("select m.*, e.*, l.*  from planner_metrics m "
                    "left join planner_errors e on m.id=e.id "
                    "left join locations l on m.remote_addr = l.ip "
                    "where m.id=%s", [objid])
        return cur.fetchone()


def get_metrics_by_version(start, end):
    with cursor() as cur:
        cur.execute("SELECT count(*), version from planner_metrics where ts > %s and ts <= %s group by version", [start, end])
        return cur.fetchall()

def get_downloads_by_version(start, end):
    with cursor() as cur:
        cur.execute("SELECT count(*), version from downloads where ts > %s and ts <= %s group by version", [start, end])
        return cur.fetchall()

def get_recent_errors(**table_args):
    columns = [(True, "e.id"),(True, "ts"), (True, "error")]
    queryClause = "select e.id, m.ts, e.error from planner_errors e left join planner_metrics m on e.id=m.id where "
    groupByClause = " group by hash "
    orderByClause = " order by count desc "
    return queryBuilder(queryClause, groupByClause, orderByClause, *columns, **table_args)

def get_recent_applications(**table_args):
    columns = [(True, "id"),(True, "ts"),(True,"hostname"), (True,"application")]
    queryClause = "select id, ts, hostname, application from planner_metrics where application is not null and "
    groupByClause = ""
    orderByClause = " order by ts desc "
    return queryBuilder(queryClause, groupByClause, orderByClause, *columns, **table_args)

def count_downloads(start=0, end=0):
    with cursor() as cur:
        cur.execute("SELECT count(*) as count FROM downloads WHERE ts>=%s AND ts <= %s", [start, end])
        return cur.fetchone()['count']

def get_recent_downloads(**table_args):
    """
    NOTE: This method does not use the query builder because of the "form_only" clause, in order to
          make it so that the clause can be used we would have to abstract that out
    :param table_args: arguments obtained from the webpage
    :return: the total count of downloads in the specified time frame, the count of downloads that match the search
             criteria, and the results of the search
    """
    with cursor() as cur:
        columns = ["id", "ts", "filename", "version", "hostname", "name", "email", "organization"]

        countClauseStart = "select count(count.id) from ("
        countClauseEnd = ") as count"
        queryClause = "select id, ts, hostname, filename, version, name, email, organization from downloads where "
        filterClause = ""
        formOnlyClause = ""
        timeRangeClause = ""
        orderClause = " order by ts desc "
        limitClause = ""

        if "filter" in table_args:
            filterValue = "%" + table_args["filter"] + "%"
            filterClause = " filename like '%s' or version like '%s' or hostname like '%s' or name like '%s' or email like '%s' or organization like '%s' and " % (filterValue, filterValue, filterValue, filterValue, filterValue, filterValue)


        if "form_only" in table_args:
            if table_args['form_only'] == 'true':
                formOnlyClause = " name is not null and email is not null and organization is not null and "

        timeRangeClause = "ts >=%s and ts <= %s" % (table_args['start_time'], table_args['end_time'])

        if "iSortCol_0" in table_args:
            orderClause = " order by %s " % (columns[table_args['iSortCol_0']])
            if table_args["sSortDir_0"] == "desc":
                orderClause = orderClause + " desc "

        if "limit" in table_args:
            limitClause = " limit %s offset %s " % (table_args["limit"], table_args["offset"])

        cur.execute(countClauseStart + queryClause + formOnlyClause + timeRangeClause + orderClause + countClauseEnd)
        totalCount = cur.fetchone()["count(count.id)"]

        cur.execute(countClauseStart + queryClause + filterClause + formOnlyClause + timeRangeClause + orderClause + countClauseEnd)
        filteredCount = cur.fetchone()["count(count.id)"]

        cur.execute(queryClause + filterClause + formOnlyClause + timeRangeClause + orderClause + limitClause)
        results = cur.fetchall()

        return totalCount, filteredCount, results

def get_runs_for_workflow(root_wf_uuid, limit=50):
    with cursor() as cur:
        if limit:
            cur.execute("SELECT * FROM dagman_metrics d  "
                        "LEFT JOIN locations l ON d.remote_addr = l.ip "
                        "WHERE d.root_wf_uuid = %s "
                        "ORDER BY d.ts LIMIT %s", [root_wf_uuid, int(limit)])
        else:
            cur.execute("SELECT * FROM pdagman_metrics d  "
                        "LEFT JOIN locations l ON d.remote_addr = l.ip "
                        "WHERE d.root_wf_uuid = %s "
                        "ORDER BY d.ts", [root_wf_uuid])
        return cur.fetchall()

def get_top_application_runs(**table_args):
    with cursor() as cur:
        columns = ["application", "runCount"]

        countClauseStart = "select count(count.application) from ("
        countClauseEnd = ") as count"
        queryClause = "select p.application application, sum(d.count) runCount from planner_metrics p, (select root_wf_uuid, count(*) count from dagman_metrics where "
        queryClause2 = " group by root_wf_uuid) d where p.root_wf_uuid = d.root_wf_uuid "
        filterClause = ""
        timeRangeClause = ""
        orderClause = " group by application order by workflows desc "
        limitClause = ""

        if "filter" in table_args:
            filterValue = "%" + table_args["filter"] + "%"
            filterClause = " and application like '%s' " % (filterValue)

        timeRangeClause = "ts >=%s and ts <= %s" % (table_args['start_time'], table_args['end_time'])

        if "iSortCol_0" in table_args:
            orderClause = " group by application order by %s " % (columns[table_args['iSortCol_0']])
            if table_args["sSortDir_0"] == "desc":
                orderClause = orderClause + " desc "

        if "limit" in table_args:
            limitClause = " limit %s offset %s " % (table_args["limit"], table_args["offset"])

        cur.execute(countClauseStart + queryClause + timeRangeClause + queryClause2 + orderClause + countClauseEnd)
        totalCount = cur.fetchone()["count(count.application)"]

        cur.execute(countClauseStart + queryClause + timeRangeClause + queryClause2 + filterClause + orderClause + countClauseEnd)
        filteredCount = cur.fetchone()["count(count.application)"]

        cur.execute(queryClause + timeRangeClause + queryClause2 + filterClause + orderClause + limitClause)
        results = cur.fetchall()

        return totalCount, filteredCount, results

def get_download(objid):
    with cursor() as cur:
        cur.execute("SELECT * FROM downloads d LEFT JOIN locations l ON d.remote_addr =l.ip WHERE d.id=%s", [objid])
        return cur.fetchone()

def get_popular_downloads(**table_args):
    columns = [(True,"filename"),(False,"count"),(False,"latest")]
    queryClause = "select filename, count(*) count, max(ts) latest from downloads where "
    groupByClause = " group by filename "
    orderByClause = " order by count desc "

    (totalCount, filteredCount, results) =  queryBuilder(queryClause, groupByClause, orderByClause, *columns, **table_args)
    return totalCount, filteredCount, results

def queryBuilder(queryClause, groupClause, orderClause, *columns, **table_args):
    """
    :param queryClause: The main clause of your query that should specify what columns you want to return and what tables you want to query
    :param groupClause: Either "" or " group by ____ "
    :param orderClause: Either "" or " order by ____ "
    :param columns: An array of tuples where the first element specifies whether or not the column is searchable, and the second specifies the column name
    :param table_args: Arguments passed down from the web page that originated the call
    :return: The total number of results, the number of results based on the search criteria, and the results of the query
    """
    with cursor() as cur:
        countClauseStart = "select count(*) from("
        countClauseEnd =") as c"
        filterClause = ""
        timeRangeClause = " (ts >= %s and ts <= %s) " % (table_args['start_time'], table_args['end_time'])
        limitClause = ""

        if "filter" in table_args:
            filterClause = " ("
            filterValue = "%" + table_args["filter"] + "%"
            for i in range(len(columns)):
                if(columns[i][0]):
                    filterClause = "%s %s like '%s' or " % (filterClause, columns[i][1], filterValue)
                if i == len(columns) - 1:
                    filterClause = filterClause.strip("or ") + ") and "

        if "iSortCol_0" in table_args:
            orderClause = " order by %s " % (columns[table_args["iSortCol_0"]][1])
            if table_args["sSortDir_0"] == "desc":
                orderClause = orderClause + " desc "

        if "limit" in table_args:
            limitClause = " limit %s offset %s " % (table_args["limit"], table_args["offset"])

        cur.execute(countClauseStart + queryClause + timeRangeClause + groupClause + countClauseEnd)
        totalCount = cur.fetchone()["count(*)"]

        cur.execute(countClauseStart + queryClause + filterClause + timeRangeClause + groupClause + countClauseEnd)
        filteredCount = cur.fetchone()["count(*)"]

        cur.execute(queryClause + filterClause + timeRangeClause + groupClause + orderClause + limitClause)
        results = cur.fetchall()

        return totalCount, filteredCount, results


def get_locations(dataset, start, end):
    """
    NOTE: We use a hardcoded limit limit of 100 only in this method
    :param dataset: Specifies what table to query and what metrics we want to get locations for
    :param start: start of the time range to look for results from
    :param end: end of the time range to look for results from
    :return: a list of locations that correspond to the dataset that was passed in
    """
    with cursor() as cur:
        if dataset.__contains__("recent"):
            if dataset.__contains__("downloads"):
                cur.execute("SELECT d.id, l.ip, l.city, l.region_name, l.country_code, l.latitude, l.longitude "
                            "FROM locations l, "
                            "(SELECT remote_addr, max(id) id from downloads WHERE ts >= %s AND ts <= %s GROUP BY remote_addr ORDER BY ts DESC) d WHERE d.remote_addr = l.ip ORDER BY l.city limit 100", [start, end])
            else:
                cur.execute("SELECT  max(m.id) id, l.ip, l.city, l.region_name, l.country_code, l.latitude, l.longitude "
                            "FROM planner_metrics m LEFT JOIN locations l ON m.remote_addr = l.ip "
                            "WHERE m.ts >= %s AND m.ts <= %s GROUP BY l.ip ORDER BY l.city, m.ts DESC limit 100", [start, end])
        elif dataset == "hostname":
            cur.execute("select h.hostname, l.ip, l.city, l.region_name, l.country_code, l.latitude, l.longitude, h.count from locations l, "
                        "(select remote_addr, hostname, count(*) count from planner_metrics where ts >= %s and ts <= %s group by hostname order by count desc) h "
                        "where l.ip = h.remote_addr limit 100", [start, end])
        results = cur.fetchall()
        return results

def get_location(ip_addr):
    with cursor() as cur:
        cur.execute("SELECT * FROM locations WHERE ip = %s", [ip_addr])
        return cur.fetchone()

def get_workflow_count_by_field(field, min, max, start, end):
    with cursor() as cur:
        query = "SELECT count(*) FROM planner_metrics WHERE %s >= %s and %s < %s and ts >= %s and ts <= %s" % (field,min,field,max,start,end)
        cur.execute(query)
        return int(cur.fetchone()["count(*)"])

def store_location(data):
    if 'latitude' not in data or \
        'longitude' not in data or \
        'country_code' not in data or \
        'region_code' not in data or \
        'region_name' not in data or \
        'city' not in data:
        log.error("Invalid location data: %s" % (data))
        return

    if 'zip_code' not in data:
        data['zip_code'] = None

    if 'metro_code' not in data:
        data['metro_code'] = None

    with cursor() as cur:
        cur.execute(
        """INSERT INTO locations (
            ip,
            country_code,
            country_name,
            region_code,
            region_name,
            city,
            zip_code,
            latitude,
            longitude,
            metro_code
        ) VALUES (
            %(ip)s,
            %(country_code)s,
            %(country_name)s,
            %(region_code)s,
            %(region_name)s,
            %(city)s,
            %(zip_code)s,
            %(latitude)s,
            %(longitude)s,
            %(metro_code)s
        )""", data)

def store_download(data):
    with cursor() as cur:
        cur.execute(
        """INSERT INTO downloads (
            id,
            ts,
            remote_addr,
            hostname,
            domain,
            version,
            filename,
            name,
            email,
            organization,
            app_domain,
            app_description,
            howheard,
            howhelp,
            oldfeatures,
            newfeatures,
            sub_users,
            sub_announce
        ) VALUES (
            %(id)s,
            %(ts)s,
            %(remote_addr)s,
            %(hostname)s,
            %(domain)s,
            %(version)s,
            %(filename)s,
            %(name)s,
            %(email)s,
            %(organization)s,
            %(app_domain)s,
            %(app_description)s,
            %(howheard)s,
            %(howhelp)s,
            %(oldfeatures)s,
            %(newfeatures)s,
            %(sub_users)s,
            %(sub_announce)s
        )""", data)

def store_planner_metrics(data):
    with cursor() as cur:
        cur.execute(
        """INSERT INTO planner_metrics (
            id,
            ts,
            remote_addr,
            hostname,
            domain,
            version,
            wf_uuid,
            root_wf_uuid,
            start_time,
            end_time,
            duration,
            exitcode,
            compute_tasks,
            dax_tasks,
            dag_tasks,
            total_tasks,
            chmod_jobs,
            inter_tx_jobs,
            compute_jobs,
            cleanup_jobs,
            dax_jobs,
            dag_jobs,
            so_tx_jobs,
            si_tx_jobs,
            create_dir_jobs,
            clustered_jobs,
            reg_jobs,
            total_jobs,
            data_config,
            application,
            dax_input_files,
            dax_inter_files,
            dax_output_files,
            dax_total_files,
            uses_pmc,
            planner_args,
            deleted_tasks,
            dax_api
        ) VALUES (
            %(id)s,
            %(ts)s,
            %(remote_addr)s,
            %(hostname)s,
            %(domain)s,
            %(version)s,
            %(wf_uuid)s,
            %(root_wf_uuid)s,
            %(start_time)s,
            %(end_time)s,
            %(duration)s,
            %(exitcode)s,
            %(compute_tasks)s,
            %(dax_tasks)s,
            %(dag_tasks)s,
            %(total_tasks)s,
            %(chmod_jobs)s,
            %(inter_tx_jobs)s,
            %(compute_jobs)s,
            %(cleanup_jobs)s,
            %(dax_jobs)s,
            %(dag_jobs)s,
            %(so_tx_jobs)s,
            %(si_tx_jobs)s,
            %(create_dir_jobs)s,
            %(clustered_jobs)s,
            %(reg_jobs)s,
            %(total_jobs)s,
            %(data_config)s,
            %(application)s,
            %(dax_input_files)s,
            %(dax_inter_files)s,
            %(dax_output_files)s,
            %(dax_total_files)s,
            %(uses_pmc)s,
            %(planner_args)s,
            %(deleted_tasks)s,
            %(dax_api)s
        )""", data)

def store_planner_errors(data):
    with cursor() as cur:
        cur.execute("""INSERT INTO planner_errors (id, error, hash)
                       VALUES (%(id)s, %(error)s, %(hash)s)""", data)

def store_dagman_metrics(data):
    with cursor() as cur:
        cur.execute(
        """INSERT INTO dagman_metrics (
            id,
            ts,
            remote_addr,
            hostname,
            domain,
            version,
            wf_uuid,
            root_wf_uuid,
            start_time,
            end_time,
            duration,
            exitcode,
            dagman_id,
            parent_dagman_id,
            jobs,
            jobs_failed,
            jobs_succeeded,
            dag_jobs,
            dag_jobs_failed,
            dag_jobs_succeeded,
            dag_status,
            planner,
            planner_version,
            rescue_dag_number,
            total_job_time,
            total_jobs,
            total_jobs_run
        ) VALUES (
            %(id)s,
            %(ts)s,
            %(remote_addr)s,
            %(hostname)s,
            %(domain)s,
            %(version)s,
            %(wf_uuid)s,
            %(root_wf_uuid)s,
            %(start_time)s,
            %(end_time)s,
            %(duration)s,
            %(exitcode)s,
            %(dagman_id)s,
            %(parent_dagman_id)s,
            %(jobs)s,
            %(jobs_failed)s,
            %(jobs_succeeded)s,
            %(dag_jobs)s,
            %(dag_jobs_failed)s,
            %(dag_jobs_succeeded)s,
            %(dag_status)s,
            %(planner)s,
            %(planner_version)s,
            %(rescue_dag_number)s,
            %(total_job_time)s,
            %(total_jobs)s,
            %(total_jobs_run)s
        )""", data)

