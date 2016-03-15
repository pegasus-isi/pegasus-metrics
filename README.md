pegasus-metrics
===============

This project is a web application for anonymous usage metrics collection and 
reporting for the Pegasus Workflow Management System.

Development
===========

Install Vagrant and VirtualBox if you don't already have them, then run:

    vagrant up

From the source directory. Once the VM is started, you can `vagrant ssh`
and then run:

    cd /vagrant
    export PEGASUS_METRICS_CONFIG=/vagrant/config.py
    python run.py

To start the server.

Production
==========

Install Python Package
----------------------

Clone the repository from GitHub and run (in a virtualenv if you prefer):

    pip install -r requirements.txt

Create MySQL Database
---------------------

Create a MySQL database and run the schema setup script:

    mysql -u pegasus -p pegasus_metrics < schema.sql

That command assumes you created a user named 'pegasus' and a schema
named 'pegasus_metrics'. The schema.sql file is in the root of the
git repository.

Create WSGI Configuration
-------------------------

Create a file called pegasus_metrics.wsgi that looks like the one in the
Git repository.

You will refer to this file in your Apache configuration.

Update Apache Configuration
---------------------------

Create a new site in your Apache configuration that looks something like this:

    <VirtualHost *:80> 
        ServerName metrics.pegasus.isi.edu
        DocumentRoot /var/www/pegasus-metrics
        CustomLog ${APACHE_LOG_DIR}/pegasus_metrics_access.log common
        ErrorLog ${APACHE_LOG_DIR}/pegasus_metrics_error.log
        LogLevel info

        WSGIDaemonProcess metrics.pegasus.isi.edu user=www-data group=www-data processes=1 threads=25
        WSGIProcessGroup metrics.pegasus.isi.edu
        WSGIScriptAlias / /var/www/pegasus-metrics/pegasus_metrics.wsgi

        <Directory /var/www/pegasus-metrics>
            Options FollowSymLinks
            AllowOverride all
        </Directory>

        # Require a password for the web UI
        <Location />
            AuthType basic
            AuthName "Pegasus Metrics"
            AuthUserFile /etc/apache2/pegasus_metrics.users
            AuthGroupFile /dev/null
            Require valid-user
        </Location>

        # Allow anyone to access /metrics with no password
        <Location /metrics>
            Allow from all
            Satisfy any
        </Location>

        # Allow isi.edu to access /status with no password
        <Location /status>
            Deny from all
            Allow from 128.9.0.0/16
            Satisfy Any
        </Location>
    </VirtualHost>

Change the ServerName, paths and authentication configuration to match your
requirements.

