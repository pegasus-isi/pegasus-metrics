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

# Apache configuration
apt-get install -y apache2 libapache2-mod-wsgi
cat > /etc/apache2/sites-available/pegasus-metrics <<END
<VirtualHost *:80>
    ServerName 127.0.0.1
    DocumentRoot /vagrant
    CustomLog \${APACHE_LOG_DIR}/pegasus_metrics_access.log common
    ErrorLog \${APACHE_LOG_DIR}/pegasus_metrics_error.log
    LogLevel info

    WSGIDaemonProcess metrics.pegasus.isi.edu user=vagrant group=vagrant processes=1 threads=25
    WSGIProcessGroup metrics.pegasus.isi.edu
    WSGIScriptAlias / /vagrant/pegasus_metrics.wsgi

    <Directory /vagrant>
        Options FollowSymLinks
        AllowOverride all
    </Directory>
</VirtualHost>
END
rm /etc/apache2/sites-enabled/000-default
service apache2 restart

