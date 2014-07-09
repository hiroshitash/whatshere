#!/bin/bash

PIDFILE=log/website_dev.pid
if [ -f $PIDFILE ]; then
    kill -9 `cat $PIDFILE`
    rm -rf $PIDFILE
fi

export WH_APP_TYPE=website


python manage.py runfcgi method=threaded host=127.0.0.1 port=8009 daemonize=false --settings=settings pidfile=$PIDFILE minspare=4 maxspare=20 maxchildren=15 maxrequests=5

