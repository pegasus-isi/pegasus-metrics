try:
    import json
except ImportError:
    import simplejson as json
import MySQLdb as mysql
from MySQLdb.cursors import DictCursor

from pegasus.metrics import app, ctx

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
            help="Database password", default="pegasus")
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
    if "db" not in dir(ctx):
        return
    ctx.db.commit()

def rollback():
    if "db" not in dir(ctx):
        return
    ctx.db.rollback()

def close():
    if "db" not in dir(ctx):
        return
    ctx.db.close()
    del ctx.db

def store_json_data(data):
    with ctx.db.cursor() as cur:
        cur.execute("INSERT INTO json_data (data) VALUES (%s)", 
                [json.dumps(data)])

def count_json_data():
    with ctx.db.cursor() as cur:
        cur.execute("SELECT count(*) as count FROM json_data")
        return cur.fetchone()['count']

def each_json_data():
    with ctx.db.cursor() as cur:
        cur.execute("SELECT id, data FROM json_data")
        for row in cur:
            if row is None:
                break
            strdata = row["data"]
            jsondata = json.loads(strdata)
            jsondata["id"] = row["id"]
            yield jsondata

def delete_planner_metrics():
    with ctx.db.cursor() as cur:
        cur.execute("DELETE FROM planner_metrics")

def delete_planner_errors():
    with ctx.db.cursor() as cur:
        cur.execute("DELETE FROM planner_errors")

def store_planner_metrics(data):
    with ctx.db.cursor() as cur:
        cur.execute(
        """INSERT INTO planner_metrics (
            id,
            ts,
            remote_addr,
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
            total_jobs
        ) VALUES (
            %(id)s,
            %(ts)s,
            %(remote_addr)s,
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
            %(total_jobs)s
        )""", data)

def store_planner_errors(data):
    with ctx.db.cursor() as cur:
        cur.execute("""INSERT INTO planner_errors (id, error) 
                       VALUES (%(id)s, %(error)s)""", data)

