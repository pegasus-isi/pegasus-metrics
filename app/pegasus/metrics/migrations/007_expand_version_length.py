
from pegasus.metrics import db

def migrate():
    cur = db.cursor()

    cur.execute("alter table planner_metrics modify version VARCHAR(32)")
    cur.execute("alter table downloads modify version VARCHAR(32)")
    cur.execute("alter table dagman_metrics modify version VARCHAR(32)")
    cur.execute("alter table dagman_metrics modify planner_version VARCHAR(32)")

    db.commit();

    cur.close();
