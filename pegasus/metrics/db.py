try:
    import json
except ImportError:
    import simplejson as json
import MySQLdb as mysql
from MySQLdb.cursors import DictCursor

from pegasus.metrics import ctx

class WithCursor(DictCursor):
    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

def add_options(parser):
    "Add database command-line options to parser"
    parser.add_option("-H", "--host", dest="host", action="store",
            help="Database hostname", default="localhost")
    parser.add_option("-P", "--port", dest="port", action="store", type="int",
            help="Database port", default=3306)
    parser.add_option("-u", "--user", dest="user", action="store", 
            help="Database username", default="pegasus")
    parser.add_option("-p", "--passwd", dest="passwd", action="store",
            help="Database password", default=None)
    parser.add_option("-D", "--db", dest="db", action="store",
            help="Database name", default="pegasus_metrics")

def connect(host="localhost", port=3306, user="pegasus", passwd="pegasus", db="pegasus_metrics"):
    if "db" in dir(ctx):
        return
    ctx.db = mysql.connect(host=host,
                           port=port,
                           user=user,
                           passwd=passwd,
                           db=db,
                           cursorclass=WithCursor,
                           use_unicode=True)

def commit():
    ctx.db.commit()

def rollback():
    ctx.db.rollback()

def close():
    ctx.db.close()
    del ctx.db

def cursor():
    return ctx.db.cursor()

def store_raw_data(ts, remote_addr, data):
    with cursor() as cur:
        cur.execute("INSERT INTO raw_data (ts, remote_addr, data) VALUES (%s, %s, %s)", 
                [ts, remote_addr, json.dumps(data)])

    return ctx.db.insert_id()

def count_raw_data(start=0):
    with cursor() as cur:
        cur.execute("SELECT count(*) as count FROM raw_data WHERE ts>=%s", [start])
        return cur.fetchone()['count']

def each_raw_data(ids=None):
    with cursor() as cur:
        query = "SELECT id, ts, remote_addr, data FROM raw_data"
        if ids is not None:
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

def count_planner_errors(start=0):
    with cursor() as cur:
        cur.execute("SELECT count(*) as count FROM planner_errors e LEFT JOIN planner_metrics m ON e.id=m.id WHERE m.ts>=%s", [start])
        return cur.fetchone()["count"]

def get_planner_stats(start=0):
    with cursor() as cur:
        cur.execute("SELECT count(*) as plans, sum(total_tasks) as tasks, sum(total_jobs) as jobs FROM planner_metrics WHERE ts>=%s", [start])
        return cur.fetchone()

def get_dagman_stats(start=0):
    with cursor() as cur:
        cur.execute("SELECT count(*) as runs, sum(total_jobs) as total_jobs, sum(total_jobs_run) as jobs_run, sum(jobs_failed+dag_jobs_failed) failed, sum(jobs_succeeded+dag_jobs_succeeded) as succeeded, sum(total_job_time)/3600.0 as total_runtime FROM dagman_metrics WHERE ts>=%s", [start])
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

def get_invalid_ids():
    with cursor() as cur:
        cur.execute("SELECT id FROM invalid_data")
        return [row["id"] for row in cur]

def get_invalid_data():
    with cursor() as cur:
        cur.execute("SELECT i.error, d.data FROM invalid_data i LEFT JOIN raw_data d ON i.id=d.id")
        return cur.fetchall()

def count_invalid_data(start=0):
    with cursor() as cur:
        cur.execute("SELECT count(*) as count FROM invalid_data i LEFT JOIN raw_data d on i.id=d.id WHERE d.ts>=%s", [start])
        return cur.fetchone()["count"]

def store_invalid_data(id, error=None):
    with cursor() as cur:
        cur.execute("INSERT INTO invalid_data (id, error) VALUES (%s, %s)", [id, error])

def get_top_hosts(limit=50, start=0):
    with cursor() as cur:
        if limit != "all":
            cur.execute("""select hostname, count(*) workflows, sum(total_tasks) tasks, sum(total_jobs) jobs
            from planner_metrics where ts>=%s group by hostname order by workflows desc limit %s""", [start, int(limit)])
        else:
            cur.execute("""select hostname, count(*) workflows, sum(total_tasks) tasks, sum(total_jobs) jobs
            from planner_metrics where ts>=%s group by hostname order by workflows desc""", [start])
        return cur.fetchall()

def get_top_domains(limit=50, start=0):
    with cursor() as cur:
        if limit != "all":
            cur.execute("""select domain, count(*) workflows, sum(total_tasks) tasks, sum(total_jobs) jobs,
            from planner_metrics  where ts>=%s group by domain order by workflows desc limit %s""", [start, int(limit)])
        else:
            cur.execute("""select domain, count(*) workflows, sum(total_tasks) tasks, sum(total_jobs) jobs,
            from planner_metrics where ts>=%s group by domain order by workflows desc""", [start])
        return cur.fetchall()

def get_top_errors(limit=50, start=0):
    with cursor() as cur:
        if limit != "all":
            cur.execute("SELECT e.hash, count(*) count, max(error) error "
                        "FROM planner_errors e LEFT JOIN planner_metrics m ON e.id=m.id "
                        "WHERE m.ts>=%s GROUP BY hash "
                        "ORDER BY count DESC LIMIT %s", [start, int(limit)])
        else:
            cur.execute("SELECT e.hash, count(*) count, max(error) error "
                        "FROM planner_errors e LEFT JOIN planner_metrics m ON e.id=m.id "
                        "WHERE m.ts>=%s GROUP BY hash "
                        "ORDER BY count DESC", [start])
        return cur.fetchall()

def get_top_applications(start, limit=50):
    with cursor() as cur:
        if limit != all:
            cur.execute("SELECT application, count(*) workflows, sum(total_tasks) tasks, sum(total_jobs) jobs "
                        "FROM planner_metrics "
                        "WHERE ts>=%s GROUP BY application "
                        "ORDER BY workflows DESC LIMIT %s", [start, int(limit)])
        else:
            cur.execute("SELECT application, count(*) workflows, sum(total_tasks) tasks, sum(total_jobs) jobs "
                        "FROM planner_metrics "
                        "WHERE ts>=%s GROUP BY application "
                        "ORDER BY workflows DESC", [start])
        return cur.fetchall()

def get_errors_by_hash(errhash):
    with cursor() as cur:
        cur.execute("select * from planner_errors where hash=%s order by id desc", [errhash])
        return cur.fetchall()

def get_metrics_and_error(objid):
    with cursor() as cur:
        cur.execute("select m.*, e.*  from planner_metrics m left join planner_errors e on m.id=e.id where m.id=%s", [objid])
        return cur.fetchone()

def get_recent_errors(limit=50):
    with cursor() as cur:
        if limit != 'all':
            cur.execute("select e.id, m.ts, e.error "
                    "from planner_errors e left join planner_metrics m on e.id=m.id "
                    "order by m.ts desc limit %s", [int(limit)])
        else:
            cur.execute("select e.id, m.ts, e.error "
                        "from planner_errors e left join planner_metrics m on e.id=m.id "
                        "order by m.ts desc")
        return cur.fetchall()

def get_recent_applications(limit=50):
    with cursor() as cur:
        if limit != 'all':
            cur.execute("select id, ts, hostname, application "
                        "from planner_metrics where application is not null "
                        "order by ts desc limit %s",[int(limit)])
        else:
            cur.execute("select id, ts, hostname, application "
                        "from planner_metrics where application is not null "
                        "order by ts desc")
        return cur.fetchall()

def count_downloads(start=0):
    with cursor() as cur:
        cur.execute("SELECT count(*) as count FROM downloads WHERE ts>=%s", [start])
        return cur.fetchone()['count']

def get_recent_downloads(limit=50):
    with cursor() as cur:
        if limit != 'all':
            cur.execute("SELECT id, ts, hostname, filename, version, name, email, organization "
                        "FROM downloads ORDER BY ts DESC LIMIT %s", [int(limit)]) # not sure why we have to call int(), but we do
        else:
            cur.execute("SELECT id, ts, hostname, filename, version, name, email, organization "
                        "FROM downloads ORDER BY ts DESC") # not sure why we have to call int(), but we do
        return cur.fetchall()

def get_download(objid):
    with cursor() as cur:
        cur.execute("SELECT * FROM downloads WHERE id=%s", [objid])
        return cur.fetchone()

def get_popular_downloads(start):
    with cursor() as cur:
        cur.execute("SELECT filename, count(*) as count, max(ts) latest "
                    "FROM downloads WHERE ts>=%s GROUP BY filename "
                    "ORDER BY count DESC, latest DESC", [start])
        return cur.fetchall()

def get_locations(dataset, limit=50):
    with cursor() as cur:
        if dataset.__contains__("recent"):
            if dataset.__contains__("downloads"):
                if limit != "all":
                    cur.execute("SELECT l.city, l.region_name, l.country_code, l.latitude, l.longitude "
                                    "FROM planner_metrics m LEFT JOIN locations l ON m.remote_addr = l.ip ORDER BY m.ts DESC LIMIT %s", [int(limit)])
                else:
                        cur.execute("SELECT l.city, l.region_name, l.country_code, l.latitude, l.longitude "
                                    "FROM planner_metrics m LEFT JOIN locations l ON m.remote_addr = l.ip ORDER BY m.ts DESC")
            else:
                if limit != "all":
                    cur.execute("SELECT l.city, l.region_name, l.country_code, l.latitude, l.longitude "
                                "FROM downloads d LEFT JOIN locations l ON d.remote_addr = l.ip ORDER BY d.ts DESC LIMIT %s", [int(limit)])
                else:
                    cur.execute("SELECT l.city, l.region_name, l.country_code, l.latitude, l.longitude "
                                "FROM downloads d LEFT JOIN locations l ON d.remote_addr = l.ip ORDER BY d.ts DESC")
        elif dataset == "downloads":
            if limit != "all":
                cur.execute("SELECT l.city, l.region_name, l.country_code, count(*) count, l.latitude, l.longitude "
                            "FROM downloads d LEFT JOIN locations l ON d.remote_addr = l.ip "
                            "GROUP BY filename ORDER BY count DESC LIMIT %s", [int(limit)])
            else:
                cur.execute("SELECT l.city, l.region_name, l.country_code, count(*) count, l.latitude, l.longitude "
                            "FROM downloads d LEFT JOIN locations l ON d.remote_addr = l.ip "
                            "GROUP BY filename ORDER BY count DESC")
        elif dataset == "domain":

            if limit != "all":
                cur.execute("SELECT l.city, l.region_name, l.country_code, count(*) workflows, l.latitude, l.longitude "
                            "FROM planner_metrics m LEFT JOIN locations l ON m.remote_addr = l.ip "
                            "GROUP BY m.domain ORDER BY workflows DESC LIMIT %s", [int(limit)])
            else:
                cur.execute("SELECT l.city, l.region_name, l.country_code, count(*) workflows, l.latitude, l.longitude "
                            "FROM planner_metrics m LEFT JOIN locations l ON m.remote_addr = l.ip "
                            "GROUP BY m.domain ORDER BY workflows DESC")
        elif dataset == "hostname":
            if limit != "all":
                cur.execute("SELECT l.city, l.region_name, l.country_code, count(*) workflows, l.latitude, l.longitude "
                            "FROM planner_metrics m LEFT JOIN locations l ON m.remote_addr = l.ip "
                            "GROUP BY m.hostname ORDER BY workflows DESC LIMIT %s", [ int(limit)])
            else:
                cur.execute("SELECT l.city, l.region_name, l.country_code, count(*) workflows, l.latitude, l.longitude "
                            "FROM planner_metrics m LEFT JOIN locations l ON m.remote_addr = l.ip "
                            "GROUP BY m.hostname ORDER BY workflows DESC")
        return cur.fetchall()

def store_location(data):
    with cursor() as cur:
        cur.execute(
        """INSERT INTO locations (
            ip,
            country_code,
            country_name,
            region_code,
            region_name,
            city,
            zipcode,
            latitude,
            longitude,
            metro_code,
            area_code
        ) VALUES (
            %(ip)s,
            %(country_code)s,
            %(country_name)s,
            %(region_code)s,
            %(region_name)s,
            %(city)s,
            %(zipcode)s,
            %(latitude)s,
            %(longitude)s,
            %(metro_code)s,
            %(area_code)s
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
            application
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
            %(application)s
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

