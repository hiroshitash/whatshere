import logging
import time
#import urllib
#import urllib2

#import django.utils.simplejson as json

#import config
import mongo_persistence_layer as mpl
import wh_facebook as whfb

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

            
def main():
    persistence = mpl.MongoPersistenceLayer()
    fb = whfb.Facebook(persistence)

    current_epoch = long(time.mktime(time.gmtime()))
    users = persistence.find_records('user', {'access_token': {"$exists": True}, 'access_token_expires': {"$gt": current_epoch}}, {'_id':1, 'access_token':1, 'uname':1})
    
    for user in users:

        preferences = persistence.find_records('preference', { 'uid': user['_id'], 'rate': {"$gt": 0.49} })
  
        #fb_places = persistence.find_records('place', {'name': "Old Pro"}, limit_num=1)
        #fb_places = persistence.PLACE.find({'name': "Old Pro"}).limit(1)
        
        for pref in preferences:
            places_nearby = []
            p = persistence.find_one_record('place', {'page_id': pref['page_id']})
            print "fb place:"
            print "Name:", p['name'], " categories:", p.get('categories'), " display_subtext", repr(p['display_subtext']), \
                " type:", p.get('type', None), " latitude:", p['latitude'], " longitude:", p['longitude'], \
                "checkin count:", p['checkin_count'], "fan count:", p['fan_count']
            query_str = p.get('categories', [])
            if len(query_str) > 0:
                query_str = query_str[0].get("name", None)
                places_nearby = fb.query_fb_nearby_places(user['access_token'], p['latitude'], p['longitude'], query=query_str)
            else:
                raise "category not found for %s" % p
        
            if len(places_nearby) > 0:
                persistence.save_similar_places(places_nearby, p['page_id'])
    

if __name__ == "__main__":
    main()
    #query_fb_neaby_place()
