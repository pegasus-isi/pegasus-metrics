#!/bin/sh

# This is to work-around the stupid apt questions for mysql
export DEBIAN_FRONTEND=noninteractive

apt-get update -y

apt-get install -y mysql-server

# These are dependencies for the python packages
apt-get install -y libmysqlclient-dev python-dev python-pip

pip install -r /vagrant/requirements.txt

# Create the database
mysql -u root <<END
create database pegasus_metrics;
create user 'pegasus'@'localhost' identified by 'pegasus';
grant all on pegasus_metrics.* to 'pegasus' identified by 'pegasus';
END
mysql -u root pegasus_metrics < /vagrant/schema.sql
