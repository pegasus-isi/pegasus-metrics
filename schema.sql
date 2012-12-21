drop table if exists raw_data;
create table raw_data (
    id INTEGER UNSIGNED NOT NULL AUTO_INCREMENT,
    data MEDIUMTEXT NOT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

drop table if exists invalid_data;
create table invalid_data (
    id INTEGER UNSIGNED NOT NULL,
    error MEDIUMTEXT NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (id) REFERENCES raw_data(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

drop table if exists planner_metrics;
create table planner_metrics (
    id INTEGER UNSIGNED NOT NULL,
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
    data_config VARCHAR(15),
    PRIMARY KEY (id),
    FOREIGN KEY (id) REFERENCES raw_data(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

drop table if exists planner_errors;
create table planner_errors (
    id INTEGER UNSIGNED NOT NULL,
    error MEDIUMTEXT,
    PRIMARY KEY (id),
    FOREIGN KEY (id) REFERENCES raw_data(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

