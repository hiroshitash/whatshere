#!/bin/bash

#python manage.py runserver 0.0.0.0:8005 2>&1 log/run_canvas_dev_http_server.log 

#openssl req -new -days 365 -nodes -out newreq.pem -keyout /etc/stunnel/stunnel.pem
#python manage.py runserver 0.0.0.0:8007 2>&1 run_canvas_dev_https_server.log 

python ./manage.py runfcgi 0.0.0.0:8007 --settings=settings maxchildren=10 \
maxspare=5 minspare=2 method=prefork socket=log/django.sock pidfile=log/django.pid 2>&1 log/run_canvas_dev_https_server.log

