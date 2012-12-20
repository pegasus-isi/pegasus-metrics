drop table if exists json_data;
create table json_data (
    id INTEGER NOT NULL AUTO_INCREMENT,
    data MEDIUMTEXT NOT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

drop table if exists planner_metrics;
create table planner_metrics (
    id INTEGER NOT NULL,
    ts DOUBLE,
    remote_addr VARCHAR(15),
    version VARCHAR(10),
    wf_uuid VARCHAR(36),
    root_wf_uuid VARCHAR(36),
    start_time DOUBLE,
    end_time DOUBLE,
    duration FLOAT,
    exitcode SMALLINT,
    compute_tasks INTEGER UNSIGNED,
    dax_tasks INTEGER UNSIGNED,
    dag_tasks INTEGER UNSIGNED,
    total_tasks INTEGER UNSIGNED,
    chmod_jobs INTEGER UNSIGNED,
    inter_tx_jobs INTEGER UNSIGNED,
    compute_jobs INTEGER UNSIGNED,
    cleanup_jobs INTEGER UNSIGNED,
    dax_jobs INTEGER UNSIGNED,
    dag_jobs INTEGER UNSIGNED,
    so_tx_jobs INTEGER UNSIGNED,
    si_tx_jobs INTEGER UNSIGNED,
    create_dir_jobs INTEGER UNSIGNED,
    clustered_jobs INTEGER UNSIGNED,
    reg_jobs INTEGER UNSIGNED,
    total_jobs INTEGER UNSIGNED,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

drop table if exists planner_errors;
create table planner_errors (
    id INTEGER NOT NULL,
    error MEDIUMTEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
