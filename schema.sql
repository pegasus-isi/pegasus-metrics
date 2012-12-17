drop table if exists json_data;
create table json_data (
    id INTEGER NOT NULL AUTO_INCREMENT,
    data MEDIUMTEXT NOT NULL,
    PRIMARY KEY (id)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

