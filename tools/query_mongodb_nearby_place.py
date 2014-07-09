import logging
import time
#import urllib
#import urllib2

#import django.utils.simplejson as json
from bson.son import SON

#import config
import mongo_persistence_layer as mpl
import wh_facebook as whfb

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

            
def main():
    persistence = mpl.MongoPersistenceLayer()

    current_epoch = long(time.mktime(time.gmtime()))
    users = persistence.find_records('user', {'access_token': {"$exists": True}, 'access_token_expires': {"$gt": current_epoch}}, 
                                     {'_id':1, 'access_token':1, 'uname':1, 'friends':1})
    
    for user in users:

        client_longitude = -122.063796997
        client_latitude = 37.2538986206 

        friend_ids = user['friends']
        uid = user['_id']
        me_friend_ids = [user['_id']] + friend_ids

        logger.debug("uid: %s", uid)
        logger.debug("num of associated users: %s", len(me_friend_ids))
        logger.debug("associated users: %s", me_friend_ids)

        import pdb;pdb.set_trace()
        #me_friend_checkins = persistence.CHECKIN.find({"loc" : {"$near": [client_longitude, client_latitude]}, "author_uid": {"$in": me_friend_ids}})
        #me_friend_checkins = persistence.CHECKIN.find({"loc" : {"$near": [client_longitude, client_latitude], "$maxDistance": 2.5}, "author_uid": {"$in": me_friend_ids}})

        s = SON({'$near': [client_longitude, client_latitude]})
        s.update({'$maxDistance': 0.5})
        me_friend_checkins = persistence.CHECKIN.find({"loc" : s, "author_uid": {"$in": me_friend_ids}})   
        #me_friend_checkins = persistence.CHECKIN.find({"loc" : s}).limit(20)

        count = me_friend_checkins.count()
        logger.debug("length of no max distance checkins: %s", count)

        for c in me_friend_checkins:                                                                                                                                              
            logger.debug("%s", c)

    

if __name__ == "__main__":
    main()
    #query_fb_neaby_place()
