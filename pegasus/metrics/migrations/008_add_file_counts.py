
from pegasus.metrics import db

def migrate():
    cur = db.cursor()

    cur.execute("alter table planner_metrics add dax_input_files int unsigned")
    cur.execute("alter table planner_metrics add dax_inter_files int unsigned")
    cur.execute("alter table planner_metrics add dax_output_files int unsigned")
    cur.execute("alter table planner_metrics add dax_total_files int unsigned")

    db.commit();

    cur.close();
