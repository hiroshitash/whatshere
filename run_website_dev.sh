#!/bin/bash

#python manage.py runserver 0.0.0.0:8005 --settings=settings maxchildren=10 \
#maxspare=5 minspare=2 method=prefork socket=log/django.sock pidfile=log/django.pid \
#2>&1 log/run_canvas_dev_http_server.log 

PIDFILE=log/website_dev.pid
LOGDIR=/var/log/whatshere_dev
if [ -f $PIDFILE ]; then
    kill -9 `cat $PIDFILE`
    rm -rf $PIDFILE
fi

#python manage.py runserver 0.0.0.0:8006 --settings=settings
export WH_APP_TYPE=website
#python manage.py runserver 0.0.0.0:8006 --settings=settings

#nohup python manage.py runfcgi 0.0.0.0:8005 --settings=settings maxchildren=10 \
#python manage.py runfcgi method=threaded host=127.0.0.1 port=8009 --settings=settings pidfile=$PIDFILE >> log/website_dev.log 2>&1 & 
#python manage.py runfcgi method=threaded host=127.0.0.1 port=8009 --settings=settings pidfile=$PIDFILE
#python manage.py runfcgi method=threaded host=127.0.0.1 port=8009 daemonize=false --settings=settings pidfile=$PIDFILE
#python manage.py runfcgi method=prefork host=127.0.0.1 port=8009 pidfile=$PIDFILE maxrequests=100 --settings=settings

nohup python manage.py runfcgi method=threaded host=127.0.0.1 port=8009 daemonize=false --settings=settings pidfile=$PIDFILE minspare=4 maxspare=20 maxchildren=15 maxrequests=5 >> $LOGDIR/website_dev.out 2>&1 &

#python ./manage.py runfcgi --settings=settings maxchildren=15 maxspare=15 minspare=2 method=prefork socket=log/django_web_dev.sock pidfile=$PIDFILE
#python ./manage.py runfcgi --settings=settings maxchildren=15 maxspare=15 minspare=2 method=prefork socket=log/django_web_dev.sock pidfile=log/website_dev.pid

#python manage.py runfcgi method=threaded host=127.0.0.1 port=8005 --settings=settings pidfile=log/djangohttp.pid maxspare=5 minspare=2
#nohup python manage.py runfcgi method=threaded host=127.0.0.1 port=8006 daemonize=false --settings=settings pidfile=$PIDFILE &
#python manage.py runfcgi method=threaded host=127.0.0.1 port=8006 daemonize=false --settings=settings pidfile=$PIDFILE
#python manage.py runserver 0.0.0.0:8007 2>&1 run_canvas_dev_https_server.log 


