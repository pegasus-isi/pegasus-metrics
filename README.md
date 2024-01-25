pegasus-metrics
===============

This project is a web application for anonymous usage metrics collection and 
reporting for the Pegasus Workflow Management System.

Development
===========

Build the Docker container

Production
==========

Create MySQL Database
---------------------

Create a MySQL database and run the schema setup script:

    mysql -u pegasus -p pegasus_metrics < schema.sql

That command assumes you created a user named 'pegasus' and a schema
named 'pegasus_metrics'. The schema.sql file is in the root of the
git repository.

Pegacorn K8s
------------

Push the built container to DockerHub pegasus/pegasus-metrics:latest

The k8s confing can be found in the k8s repo under
clusters/pegacorn/pegasus/pegasus-metrics-fe/


