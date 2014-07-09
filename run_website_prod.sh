#!/bin/bash

PIDFILE=log/website_prod.pid
LOGDIR=/var/log/whatshere_prod

if [ -f $PIDFILE ]; then
    kill -9 `cat $PIDFILE`
    rm -rf $PIDFILE
fi

export WH_APP_TYPE=website

nohup python manage.py runfcgi method=threaded host=127.0.0.1 port=8010 daemonize=false --settings=settings pidfile=$PIDFILE minspare=4 maxspare=20 maxchildren=15 maxrequests=5 >> $LOGDIR/website_prod.out 2>&1 &

#python manage.py runfcgi method=threaded host=127.0.0.1 port=8010 daemonize=false --settings=settings pidfile=$PIDFILE minspare=4 maxspare=20 maxchildren=15 maxrequests=5 


