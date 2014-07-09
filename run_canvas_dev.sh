#!/bin/bash

#python manage.py runserver 0.0.0.0:8005 --settings=settings maxchildren=10 \
#maxspare=5 minspare=2 method=prefork socket=log/django.sock pidfile=log/django.pid \
#2>&1 log/run_canvas_dev_http_server.log 

PIDFILE=log/canvas_dev.pid
LOGDIR=/var/log/whatshere_dev

if [ -f $PIDFILE ]; then
    kill -9 `cat $PIDFILE`
    rm -rf $PIDFILE
fi
export WH_APP_TYPE=canvas

#python manage.py runserver 0.0.0.0:8005 --settings=settings maxchildren=10 \
#nohup python manage.py runfcgi 0.0.0.0:8005 --settings=settings maxchildren=10 \
#python manage.py runfcgi 0.0.0.0:8005 --settings=settings maxchildren=10 \
#maxspare=5 minspare=2 method=prefork socket=log/django.sock pidfile=log/djangohttp.pid \
#2>&1 log/run_canvas_dev_http_server.log 
#python manage.py runfcgi method=threaded host=127.0.0.1 port=8005 --settings=settings pidfile=log/djangohttp.pid maxspare=5 minspare=2

nohup python manage.py runfcgi method=threaded host=127.0.0.1 port=8004 daemonize=false --settings=settings pidfile=$PIDFILE minspare=4 maxspare=20 maxchildren=15 maxrequests=5 >> $LOGDIR/canvas_dev_nohup.out 2>&1 &

#python manage.py runserver 0.0.0.0:8007 2>&1 run_canvas_dev_https_server.log 


