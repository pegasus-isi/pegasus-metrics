from pegasus.metrics import db


def migrate():
    cur = db.cursor()

    cur.execute("alter table planner_metrics add dax_api VARCHAR(15)")

    db.commit()

    cur.close()
