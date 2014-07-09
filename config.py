'''
Created on Jul 1, 2012
@author: hiroshitashiro
'''

import os

# DB Layer related
#URL_MONGODB = '10.170.109.168'
URL_MONGODB = 'ec2-184-72-8-4.us-west-1.compute.amazonaws.com'
PORT_MONGODB = 27017


dev = True
PyDev = False

# app type can be canvas or website
APP_TYPE = os.environ.get('WH_APP_TYPE', 'canvas')
#import pdb; pdb.set_trace()
if APP_TYPE == "website":
    FLAG_INDIVIDUAL_WEBSITE = True
else:
    FLAG_INDIVIDUAL_WEBSITE = False

#if PyDev:
#    WEBSITE_HOST="localhost:8006"
#    WH_DOMAIN=".localhost.com"
#else:

WH_DOMAIN=".whatshereapp.com"

GROUPON_CLIENT_ID = "1dff88422a9bfe2be21e99c4355cdd5a4a817f87"

COMISSION_JUNCTION_PID = '7082341'
COMISSION_JUNCTION_REDIRECT_URL ="http://www.anrdoezrs.net/click-%s-10804307" % COMISSION_JUNCTION_PID

if not dev:
    # FB related
    FACEBOOK_APP_ID = "178504128874319"
    FACEBOOK_APP_SECRET = "1947d6668bc2e9dc7c5ca25002dd7fde"
    FACEBOOK_CANVAS_PAGE = "https://apps.facebook.com/whatshereapp"
    EC2_APP_PAGE = "http://ec2-50-18-94-46.us-west-1.compute.amazonaws.com:8000"
    DB_NAME_MONGODB = 'whatshere'
    WEBSITE_HOST="http://whatshereapp.com"
else:
    FACEBOOK_APP_ID = "405781629467506"
    FACEBOOK_APP_SECRET = "f69a3f556cc85f728e2f138894aa9431"
    FACEBOOK_CANVAS_PAGE = "https://apps.facebook.com/whatsheredev"
#    EC2_APP_PAGE = "http://ec2-50-18-94-46.us-west-1.compute.amazonaws.com:8005"
    EC2_APP_PAGE = "//ec2-50-18-94-46.us-west-1.compute.amazonaws.com:8005"
    DB_NAME_MONGODB = 'whatsheredev'
    WEBSITE_HOST="http://whatshereapp.com:8006"

#FACEBOOK_PERMISSIONS_SCOPE = "offline_access,read_stream,user_checkins,friends_checkins,user_events"
FACEBOOK_PERMISSIONS_SCOPE = "user_interests,user_likes,user_checkins,friends_checkins,user_events,user_status,friends_status"
APP_FB_ACCESS_TOKEN = "178504128874319|lksL6sQ5E0Ee091nZbYB1fahaek"
APP_FB_ACCESS_TOKEN_GRANT_TYPE = "client_credentials"

NUM_NEARBY_PLACES_QUERY = 25
NUM_PLACES_FOR_LIST = 300

MAX_MAP_SIZE = 10000
NUM_ENTRY_PER_PAGE = 20
