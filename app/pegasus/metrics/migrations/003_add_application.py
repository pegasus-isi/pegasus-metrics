
from pegasus.metrics import db

def migrate(conn):
    cur = db.cursor()

    cur.execute("ALTER TABLE planner_metrics ADD (application VARCHAR(256))")

    db.commit()

    cur.close()

