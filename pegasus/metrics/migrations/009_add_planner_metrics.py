
from pegasus.metrics import db

def migrate():
    cur = db.cursor()

    cur.execute("alter table planner_metrics add uses_pmc BOOLEAN")
    cur.execute("alter table planner_metrics add planner_args TEXT")
    cur.execute("alter table planner_metrics add deleted_tasks INTEGER UNSIGNED")

    db.commit();

    cur.close();
