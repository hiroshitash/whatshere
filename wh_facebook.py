'''
Created on Jul 1, 2012

@author: hiroshitashiro

Description: Responsible for facebook interactions: running fql queries, graph api etc.

'''

import base64
import Cookie
from datetime import datetime
import email.utils
import hashlib
import hmac
from httplib import BadStatusLine
import logging
import re
import sys
import time
import traceback
import urllib
import urllib2
import util

import django.utils.simplejson as json

import config


logger = logging.getLogger(__name__)
#logging.basicConfig(level=logging.DEBUG)
#logger = logging.getLogger(__name__)


# FQL queries
_me_query =          'SELECT uid, name FROM user WHERE uid = me()'
_friend_name_query = 'SELECT uid, name FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE uid1 = me())'

_my_checkin_query =  'SELECT target_id, target_type, author_uid, coords, tagged_uids, message, timestamp FROM checkin WHERE author_uid = me() order by timestamp'

_friend_checkin_query = 'SELECT target_id, target_type, author_uid, coords, tagged_uids, message, timestamp '
_friend_checkin_query +=    'FROM checkin WHERE author_uid IN '
_friend_checkin_query +=    '(SELECT uid2 FROM friend WHERE uid1 = me()) order by author_uid'

_base_page_query = 'SELECT page_id, page_url, pic_small, pic, fan_count, type, website, general_info, location, '
_base_page_query += 'parking, hours, public_transit, attire, payment_options, price_range, phone, culinary_team, categories '
_base_page_query +=      'FROM page WHERE page_id '

_page_query = _base_page_query + ' IN '
_page_query +=          '(SELECT target_id FROM checkin WHERE author_uid = me() OR author_uid IN '
_page_query +=              '(SELECT uid2 FROM friend WHERE uid1 = me())) order by page_id'

_base_location_query = 'SELECT page_id, name, description, longitude, latitude, checkin_count, display_subtext '
_base_location_query +=     'FROM place WHERE page_id '
_location_query = _base_location_query + ' IN '
_location_query +=          '(SELECT target_id FROM checkin WHERE author_uid = me() OR author_uid IN '
_location_query +=              '(SELECT uid2 FROM friend WHERE uid1 = me())) order by page_id'

_page_equal_query_tmpl = _base_page_query + ' = %s'
_location_equal_query_tmpl = _base_location_query + ' = %s'

_page_bulk_query_tmpl = _base_page_query + ' IN (%s)'
_location_bulk_query_tmpl = _base_location_query + ' IN (%s)'

_base_query_pair = '"%s":"%s"'
_me_query_pair = _base_query_pair % ("me_query", _me_query)
_friend_name_query_pair = _base_query_pair % ("friend_name_query", _friend_name_query)
_my_checkin_query_pair = _base_query_pair % ("my_checkin_query", _my_checkin_query)
_friend_checkin_query_pair = _base_query_pair % ("friend_checkin_query", _friend_checkin_query)
_page_query_pair = _base_query_pair % ("page_query", _page_query)
_location_query_pair = _base_query_pair % ("location_query", _location_query)

DAY_IN_SECS = 60 * 60 * 24
DISTANCE_QUERY_SIMILAR_PLACES_MILES = 100
MAX_COUNT_QUERY_SIMILAR_PLACES_PER_USER = 150

class SyncFacebookDBException (Exception):
    pass

class Facebook(object):
    '''
    classdocs
    '''
    _map_fb_id_cache = {}
    
    def __init__(self, persistence=None):
        '''
        Constructor
        '''
        self._persistence = persistence
    
    
    def set_db_driver(self, persistence):
        self._persistence = persistence
        

    def get_extended_access_token_w_timeout(self, access_token, access_token_expires, timeout=60*60*24):
        current_time_epoch = time.mktime(time.gmtime())
        if access_token_expires is None or (access_token_expires - current_time_epoch) < timeout:
            return self.get_extended_access_token(access_token, access_token_expires)
        return access_token, access_token_expires

        
    def get_extended_access_token(self, access_token, access_token_expires):
        ext_at_url = "https://graph.facebook.com/oauth/access_token?client_id=%s&client_secret=%s&grant_type=fb_exchange_token&fb_exchange_token=%s" % \
            (config.FACEBOOK_APP_ID, config.FACEBOOK_APP_SECRET, access_token)
        logger.debug("ext_at_url: %s", ext_at_url)
        try:
            f = urllib2.urlopen(ext_at_url)
            new_access_token_str = f.read()
            try:
                new_access_token_params = dict([p.split('=') for p in new_access_token_str.split('&')])
            except:
                new_access_token_params = {}
        except urllib2.HTTPError as e:
            msg = e.fp.fp._sock.msg.dict['www-authenticate']
            logger.warn("Extending access token failed. %s", msg)
            logger.warn("ext_at_url: %s", ext_at_url)
            return access_token, access_token_expires  # return the original 
        
        current_time_epoch = long(time.mktime(time.gmtime()))
        return new_access_token_params.get('access_token', access_token), long(new_access_token_params.get('expires', access_token_expires)) + current_time_epoch


    def sync_user_access_token(self):
        #users = self._persistence.find_records('user', {'access_token':{"$exists": 1}}, {"name":1, "access_token":1, "last_update":1})
        current_time_epoch = time.mktime(time.gmtime())
        expire_in_aday = current_time_epoch + DAY_IN_SECS * 2
        users = self._persistence.find_records('user',
                                               {'access_token':{"$exists": 1}, 'access_token_expires':{"$lt": expire_in_aday},
                                                'access_token_expires':{"$gt": current_time_epoch}
                                                },
                                               {"name":1, "access_token":1, 'access_token_expires':1})
        for user in users:
            #import pdb; pdb.set_trace()
            logger.info("Going to extend access token for user %s: %s.", user['name'], user['access_token'])
            new_access_token, new_access_token_expires = self.get_extended_access_token(user['access_token'], user['access_token_expires'])
            logger.info("New access token: %s, expires:%s", new_access_token, new_access_token_expires)

            self._persistence.update('user', {"_id": user['_id']},
                                     { "$set": {"access_token":new_access_token, "access_token_expires":new_access_token_expires} })
            
        
    def query_fb_and_save(self, access_token, access_token_expires, client_loc_longitude, client_loc_latitude):
        #import pdb; pdb.set_trace()
        try:
            logger.debug("query_fb_and_save start")

            # save access_token first
            self._persistence.save_list_objects('access_token', [{"_id": access_token, "last_update": datetime.now()}])

            fql_queries = '{%s,%s,%s,%s,%s,%s}' % (_me_query_pair,_friend_name_query_pair,_my_checkin_query_pair,
                                                  _friend_checkin_query_pair,_page_query_pair,_location_query_pair)

            logger.debug("fql_queries: %s", fql_queries)
    
            fql_queries = urllib.quote_plus(fql_queries)
            fql_queries_url = "https://api.facebook.com/method/fql.multiquery?access_token=%s&queries=%s&format=json" % \
                (access_token, fql_queries)

            logger.info("\nfql_queries_url: %s", fql_queries_url)

            try:
                f = urllib2.urlopen(fql_queries_url)
            except BadStatusLine, e:
                logger.error("\nBadStatusLine: %s\nTrying again in 5 secs", e)
                time.sleep(5)
                try:
                    f = urllib2.urlopen(fql_queries_url)
                except BadStatusLine, e:
                    logger.error("\nBadStatusLine: %s", e)

            fql_result_json = json.loads(f.read())
            logger.debug("\nfql_result_json: %s", fql_result_json)
    
            if (type(fql_result_json) == type({}) and fql_result_json.get('error_code', 0) > 0):
                logger.error("\nfql_result_json error_code: %s", fql_result_json.get('error_code'))
                return
    
            me_elem = None
            fname_list = None
            my_checkin_list = None
            friend_checkin_list = None
            page_list = None
            location_list = None
            for elem in fql_result_json:
                if elem.get('name') == 'me_query':
                    me_elem = elem.get('fql_result_set')[0]
                elif elem.get('name') == 'friend_name_query':
                    fname_list = elem.get('fql_result_set')
                elif elem.get('name') == 'my_checkin_query':
                    my_checkin_list = elem.get('fql_result_set')
                elif elem.get('name') == 'friend_checkin_query':
                    friend_checkin_list = elem.get('fql_result_set')
                elif elem.get('name') == 'page_query':
                    page_list = elem.get('fql_result_set')
                elif elem.get('name') == 'location_query':
                    location_list = elem.get('fql_result_set')
                else:
                    logger.warn("unknown query found. %s", elem)

            logger.debug("\n\nme_elem: %s", me_elem)
            logger.debug("\n\nfname_list: %s", fname_list)
            logger.debug("\n\my_checkin_list: %s", my_checkin_list)
            logger.debug("\n\friend_checkin_list: %s", friend_checkin_list)
            logger.debug("\n\npage_list: %s", page_list)
            logger.debug("\n\location_list: %s", location_list)
    
            # construct friend id list and friend name list
            friend_id_list = []
            fname_hash = {}
            for fname in fname_list:
                friend_id_list.append(long(fname['uid']))
                fname_hash[long(fname['uid'])] = fname['name']
            logger.debug("\n\nfriend_id_list: %s", friend_id_list)
            logger.debug("\n\nfname_hash: %s" % fname_hash)

            # save user me
            my_checkin_list_filtered = []
            for checkin in my_checkin_list:
                self.convert_checkin_coord_data(checkin)
                checkin['uname'] = me_elem['name']
                if checkin.get('target_type', None) is not None and checkin['target_type'] == 'page':
                    my_checkin_list_filtered.append(checkin)
                    
            logger.debug("access_token:%s, me_elem:%s", access_token, me_elem)
    
            self._persistence.save_list_objects('user', [{"_id":long(me_elem['uid']), "name":me_elem['name'], "access_token":access_token,
                                       "access_token_expires":access_token_expires, "last_update": datetime.now(), "friends":friend_id_list,
                                       "checkin":my_checkin_list_filtered}])
     
            # construct friend checkin list
            fcheckin_hash = {}
            friend_checkin_list_filtered = []
            for checkin in friend_checkin_list:
                self.convert_checkin_coord_data(checkin)
                checkin["uname"] = fname_hash[long(checkin['author_uid'])]

                if checkin.get('target_type', None) is not None and checkin['target_type'] == 'page':
                    if fcheckin_hash.has_key(long(checkin['author_uid'])):
                        fcheckin_hash[long(checkin['author_uid'])].append(checkin)
                    else:
                        fcheckin_hash[long(checkin['author_uid'])] = [checkin]
                    friend_checkin_list_filtered.append(checkin)
            logger.info("\n\nfcheckin_hash: %s", fcheckin_hash)
    
            # save friend users
            for fid in friend_id_list:
                logger.debug("fid: %s\n", fid)
                logger.debug("fname_hash[%s]: %s\n", fid, fname_hash[long(fid)])
                logger.debug("\n\nfcheckin_hash[%s]: %s", fid, fcheckin_hash.get(long(fid), None))
                self._persistence.update('user', {"_id": long(fid)},
                                   { "$set": {"name":fname_hash[long(fid)], "checkin":fcheckin_hash.get(long(fid), None)} },
                                   True)
    
            # save user's and friends' checkins to collection checkin
            # when embeded search is begun to be supported, we can remove this part.
            self._persistence.save_list_objects('checkin', my_checkin_list_filtered)
            self._persistence.save_list_objects('checkin', friend_checkin_list_filtered)
        
            # Merge page and place if same page_id
            idx_page = 0
            for idx,place in enumerate(location_list):
                logger.info("\n\nplace: %s", place)
                place['_id'] = long(place['page_id'])
                place['loc'] = [place['longitude'], place['latitude']]
                place['access_token_uid'] = long(me_elem['uid'])

                while place['page_id'] > page_list[idx_page]['page_id']:
                    idx_page += 1
                page = page_list[idx_page]
    
                if long(place['page_id']) == long(page['page_id']):
                    location_list[idx] = dict(place.items() + page.items())
                else:
                    raise SyncFacebookDBException("Page ID of place and page did not match.")
                location_list[idx]['last_update'] = datetime.now()

            # save locations
            logger.debug("\n\nlocation_list to be saved in mongodb: %s", location_list)
            self._persistence.save_list_objects('place', location_list)
    
            # save user's likes
            self.save_likes(access_token, me_elem['uid'])
            
            rate_list = self._persistence.trigger_fill_coll_preference(me_elem['uid'], friend_id_list)
            #import pdb; pdb.set_trace()
            self.query_save_similar_places(rate_list, access_token, client_loc_longitude, client_loc_latitude)
        except Exception, e:
            util.log_exception_error(logger, "query_fb_and_save failed. %s" % e)
        except:
            util.log_exception_error(logger, "Unexpected error at query_fb_and_save failed.")
            raise
        return


    def query_save_similar_places(self, rate_list, user_access_token, client_loc_longitude, client_loc_latitude):
        #import pdb; pdb.set_trace()
        logger.info("rate_list: %s, user_access_token:%s, client_loc_longitude:%s, client_loc_latitude:%s" % (rate_list, user_access_token, client_loc_longitude, client_loc_latitude))
        try:
            client_loc_longitude = float(client_loc_longitude)
            client_loc_latitude = float(client_loc_latitude)
        except:
            logger.error("client_loc_longitude:%s or client_loc_latitude:%s is not number" % (client_loc_longitude, client_loc_latitude))

        count = 0
        for pref in rate_list:
            places_nearby = []

            # skip if already saved or exceeds max query counts
            if self._persistence.is_similar_places_saved(pref['page_id']) or count > MAX_COUNT_QUERY_SIMILAR_PLACES_PER_USER:
                continue
            p = self._persistence.find_one_record('place', {'page_id': pref['page_id']})

            if p is not None and p.get('categories', None) is not None and p.get('latitude', None) is not None and \
                    p.get('longitude', None) is not None:
                logger.debug("fb place - Name:%s, categories:%s, display_subtext:%s, type:%s, latitude:%s, longitude:%s, checkin count:%s, fan count:%s", \
                                     repr(p['name']), repr(p.get('categories', None)), repr(p.get('display_subtext', None)), repr(p.get('type', None)), \
                                     p['latitude'], p['longitude'], p.get('checkin_count', None), p.get('fan_count', None))                    
                distance_appr = util.calc_approximate_distance((client_loc_longitude, client_loc_latitude), (p['longitude'], p['latitude'])) 

                query_str = p.get('categories', [])
                if len(query_str) > 0 and distance_appr < DISTANCE_QUERY_SIMILAR_PLACES_MILES:
                    query_str = query_str[0].get("name", None)
                    places_nearby = self.query_fb_nearby_places(user_access_token, p['latitude'], p['longitude'], query=query_str)
                    count += 1
                else:
                    logger.error("category not found or not close enougn (%smi)for %s", distance_appr, p)
        
                if len(places_nearby) > 0:
                    self._persistence.save_similar_places(places_nearby, p['page_id'])
            else:
                logger.error("place or its category is None. Skipping %s", p)
#        import pdb; pdb.set_trace()
        logger.info("Total of %s similar places queried.", count)

    
    def query_fql_bulk(self, list_target_ids, fql_query_tmpl, acess_token):
        #target_id = Facebook._map_fb_id_cache.get(target_id, target_id)
        
        str_target_ids = ",".join(list_target_ids)
        flag_try = True
        while flag_try:
            fql_query = fql_query_tmpl % str_target_ids
            fql_query_url = "https://api.facebook.com/method/fql.query?query=%s&format=json&access_token=%s" % \
                (urllib.quote_plus(fql_query), acess_token)
            
            #import pdb; pdb.set_trace()
            try:
                f = urllib2.urlopen(fql_query_url)
            except urllib2.HTTPError, e:
                logger.warn("querying_fql_bulk failed. %s\n trying again.\nfql_query_url:%s", e, fql_query_url)
                time.sleep(30)                
                try:
                    f = urllib2.urlopen(query_url)
                except urllib2.HTTPError, e:
                    logger.warn("querying_fql_bulk 2nd attempt failed.")
                    #import pdb; pdb.set_trace()
                    break

            fql_result_json = json.loads(f.read())
            logger.debug("fql_result_json: %s", fql_result_json)
        
            if (type(fql_result_json) == type({}) and fql_result_json.get('error_code', 0) > 0):
                logger.error("fql_result_json error_code: %s", fql_result_json.get('error_code'))
                logger.error("failed url: %s", fql_query_url)
                raise SyncFacebookDBException("fql_result_json error_code: %s" % fql_result_json.get('error_code'))

            #if fql_result_json == []:
            #    # try graph api
            #    new_target_id = self.get_newid_attemp_w_graph_api(target_id, acess_token)
            #    flag_try = (long(new_target_id) != long(target_id))
            #    target_id = new_target_id
            #else:
            flag_try = False
        return fql_result_json
    

    def query_fql_equal(self, target_id, fql_query_tmpl, acess_token):
        target_id = Facebook._map_fb_id_cache.get(target_id, target_id)
        
        flag_try = True
        while flag_try:
            fql_query = fql_query_tmpl % target_id
            fql_query_url = "https://api.facebook.com/method/fql.query?query=%s&format=json&access_token=%s" % \
                (urllib.quote_plus(fql_query), acess_token)
            
            #import pdb; pdb.set_trace()            
            f = urllib2.urlopen(fql_query_url)
            fql_result_json = json.loads(f.read())
            logger.debug("fql_result_json: %s", fql_result_json)
        
            if (type(fql_result_json) == type({}) and fql_result_json.get('error_code', 0) > 0):
                logger.error("fql_result_json error_code: %s", fql_result_json.get('error_code'))
                logger.error("failed url: %s", fql_query_url)
                raise SyncFacebookDBException("fql_result_json error_code: %s" % fql_result_json.get('error_code'))

            if fql_result_json == []:
                # try graph api
                new_target_id = self.get_newid_attemp_w_graph_api(target_id, acess_token)
                flag_try = (long(new_target_id) != long(target_id))
                target_id = new_target_id
            else:
                flag_try = False
        return fql_result_json

    
    def get_newid_attemp_w_graph_api(self, old_target_id, acess_token):
        try:
            graph_api_url = "https://graph.facebook.com/%s?access_token=%s" % (old_target_id, acess_token)
            f = urllib2.urlopen(graph_api_url)
            graph_api_json = json.loads(f.read())
            if graph_api_json == False:
                logger.error("graph api returned False. probably target page has age/private restriction.")
            else:
                logger.error("graph api works but fql doesn't. %s", graph_api_url)
            return old_target_id
        except urllib2.HTTPError as e:
            msg = e.fp.fp._sock.msg.dict['www-authenticate']
            if msg is not None:
                pattern = r".* ID (\d*).* to .* ID (\d*)\. .*"
                matches = re.match(pattern, msg)
                if matches:
                    old_id = matches.group(1)
                    new_id = matches.group(2)
                    if long(old_id) == long(old_target_id):
                        if len(Facebook._map_fb_id_cache) > config.MAX_MAP_SIZE:
                            Facebook._map_fb_id_cache = {}
                        Facebook._map_fb_id_cache[long(old_id)] = long(new_id)
                        logger.info("new id %s found from old id %s", new_id, old_id)
                        return new_id
                    else:
                        logger.error("new id not found from graph api. %s", graph_api_url)
                        return old_target_id
                else:
                    logger.error("new id not found from graph api. %s", graph_api_url)
                    return old_target_id
            else:
                logger.error("graph api failed. %s", repr(e))
                return old_target_id


    def query_fb_nearby_places(self, user_access_token, latitude, longtitude, distance=1000, query='fun', limit_num_places=config.NUM_NEARBY_PLACES_QUERY):
        logger.info("query: %s" % query)
        base_url = "https://graph.facebook.com/search?type=place"
        url_str_list = []
        url_str_list.append(base_url)
        if query is None or len(query) == 0:
            return []

        if isinstance(query, unicode):
            query = query.encode('utf-8')
        query_param = "&q=%s" % urllib.quote_plus(query)
        url_str_list.append(query_param)

        if latitude is not None and longtitude is not None and isinstance(distance, int):
            loc_param = "&center=%s,%s&distance=%s" % (latitude, longtitude, distance)
            url_str_list.append(loc_param)
        other_param = "&access_token=%s&format=json" % (user_access_token)
        url_str_list.append(other_param)
    
        query_url = "".join(url_str_list)
        logger.info("\nquery_url: %s" % query_url)
        
        list_page_ids = []

        while query_url is not None and len(list_page_ids) < limit_num_places:
            try:
                f = urllib2.urlopen(query_url)
            except urllib2.HTTPError, e:
                logger.warn("querying nearby similar place failed. %s\nquery_url:%s", e, query_url)
                #import pdb; pdb.set_trace()
                time.sleep(30)
                try:
                    f = urllib2.urlopen(query_url)
                except urllib2.HTTPError, e:
                    logger.warn("querying nearby similar place 2nd attempt failed.")
                    break
            query_result_json = json.loads(f.read())
            #import pdb; pdb.set_trace()
            logger.debug("\nquery_result_json: %s" % query_result_json)       
            page = query_result_json.get('paging', None)
            if page is not None:
                query_url = page.get("next", None)
                data = query_result_json.get('data', None)

                print "\tpage: %s" % page
                if data is not None:
                    for p in data:
                        print "\t",p
                        if len(list_page_ids) < limit_num_places:
                            list_page_ids.append(p['id'])
            else:
                query_url = None
                        
        if len(list_page_ids) > 0:
            json_pages_result     = self.query_fql_bulk(list_page_ids, _page_bulk_query_tmpl, user_access_token)
            json_locations_result = self.query_fql_bulk(list_page_ids, _location_bulk_query_tmpl, user_access_token)
            
            if len(json_pages_result) != len(json_locations_result):
                logger.warn("length of json_pages_result(%s) and json_locations_result(%s) differ.", len(json_pages_result), len(json_locations_result))

            page_hash = {}
            for page in json_pages_result:
                page['page_id'] = long(page['page_id'])
                page_hash[page['page_id']] = page
                
            merged_place_list = []
            for loc in json_locations_result:
                #import pdb;pdb.set_trace()
                page = page_hash.get(loc['page_id'], {})
                if page == {}:
                    logger.debug("Page not found for %s", loc)
                place = dict(loc.items() + page.items())
                place['loc'] = [place['longitude'], place['latitude']]
                place['last_update'] = datetime.now()
                merged_place_list.append(place)
            return merged_place_list
        else:
            return []
            

    def sync_place_db(self):
        places = self._persistence.find_records('place', {'categories':{"$exists": 0}}, {'page_id':1, 'access_token_uid':1})
        app_access_token = self.get_app_access_token()
        
        for place in places:
            #print "place id:", place["_id"], "page_id:", place["page_id"], "name:", place["name"]
            #if place.get('categories', None) is not None:
            #    continue

            print "before place: %s" % place
            place_orig = place.copy()


            result_query_list = [{'query':_page_equal_query_tmpl, 'result':None}, {'query':_location_equal_query_tmpl, 'result':None}]
            for i in [0, 1]:
                result_query_list[i]['result'] = self.query_fql_equal(place['page_id'], result_query_list[i]['query'], app_access_token)
            
                if result_query_list[i]['result'] == []:
                    if place.get('access_token_uid', None) is not None:
                        user_access_token = self._persistence.find_one_record('user', {"_id": place['access_token_uid']}, {"access_token": 1})
                        result_query_list[i]['result'] = self.query_fql_equal(place['page_id'], result_query_list[i]['query'], user_access_token)
                
                    if result_query_list[i]['result'] == []:
                        current_time_epoch = time.mktime(time.gmtime())
                        users = self._persistence.find_records('user', 
                                               {'access_token':{"$exists": 1}, 'access_token_expires':{"$gt": current_time_epoch}}, 
                                               {"access_token":1})
                        for user in users:
                            result_query_list[i]['result'] = self.query_fql_equal(place['page_id'], result_query_list[i]['query'], user['access_token'])
                            if result_query_list[i]['result'] != []:
                                break
            
            fql_page_result_json = result_query_list[0]['result']
            fql_place_result_json = result_query_list[1]['result']
            
            if(len(fql_page_result_json) == 0 and len(fql_place_result_json) == 0):
                    logger.warn("Cannot get page info. Skipping page ID %s", place['page_id'])
            else:
                if len(fql_page_result_json) == 0:
                    place = fql_place_result_json[0]
                elif len(fql_place_result_json) == 0:
                    place = fql_page_result_json[0]
                else:
                    place = dict(fql_place_result_json[0].items() + fql_page_result_json[0].items())
                place['_id'] = long(place['page_id'])
                place['last_update'] = datetime.now()

                print "after place: %s" % place
                if place_orig['_id'] != place['_id']:
                    # You cannot update _id. You'll have to save the document using a new _id, and then remove the old document.
                    self._persistence.remove('place', {"_id": {"$in": [str(place_orig['_id']), long(place_orig['_id'])]}})
                    self._persistence.save('place', place)
                
                    self._persistence.update('checkin', {'page_id': {"$in": [str(place_orig['page_id']), long(place_orig['page_id'])]}}, 
                                         {'page_id': long(place['page_id'])}, multi=True)
                else:
                    self._persistence.save('place', place)


    def get_app_access_token(self):
        app_ac_token_url = "https://graph.facebook.com/oauth/access_token?client_id=%s&client_secret=%s&grant_type=%s&redirect_uri=%s" % \
                            (config.FACEBOOK_APP_ID, config.FACEBOOK_APP_SECRET, config.APP_FB_ACCESS_TOKEN_GRANT_TYPE, config.FACEBOOK_CANVAS_PAGE)
        app_ac_token = None
        try:
            f = urllib2.urlopen(app_ac_token_url)
            pattern = r"access_token=(.*)"
            ac_token_str = f.read()
            matches = re.match(pattern, ac_token_str)
            if matches:
                app_ac_token = matches.group(1)
            else:
                logger.warn("Getting app access token failed. Access token not fount given %s", ac_token_str)
        except urllib2.HTTPError, e:
            msg = e.fp.fp._sock.msg.dict['www-authenticate']
            logger.warn("Getting app access token failed. %s", msg)
        return app_ac_token

    
    def convert_checkin_coord_data(self, checkin):
        checkin["_id"] = "%s_%s" % (checkin["author_uid"], checkin['target_id'])
        if checkin.get("coords", None) != None and isinstance(checkin["coords"], dict) and checkin["coords"].get("longitude", None) != None and \
            checkin["coords"].get("latitude", None) != None:
            checkin["loc"] = [checkin["coords"]["longitude"], checkin["coords"]["latitude"]]
            del checkin["coords"]
        else:
            logger.warn("checkin:%s has no coords" % checkin)
            
        

    def save_likes(self, access_token, uid):    
        # save user's likes
        try:
            likes_url = "https://graph.facebook.com/me/likes?access_token=%s" % access_token
            f = urllib2.urlopen(likes_url)
            likes_result_json = json.loads(f.read())
            logger.debug("\nlikes_result_json: %s" % likes_result_json)
            flag = True
            like_list = []

            while flag:
                for like in likes_result_json.get('data', []):
                    like['_id'] = long(uid)
                    like_list.append(like)
                    logger.info("name:%s, id:%s, category:%s",
                                like.get('name', None), like.get('id', None), like.get('category', None))

                next_page = likes_result_json.get('paging', {}).get('next', None)
                logger.debug("next_page:%s", next_page)
                flag = False
                if next_page is not None:
                    flag = True
                    f = urllib2.urlopen(next_page)
                    likes_result_json = json.loads(f.read())

            self._persistence.save_list_objects('like', like_list)
        except urllib2.HTTPError, e:
            #import pdb; pdb.set_trace()
            logger.error("Saving user %s likes failed on table like. Possibly expired access token. %s. error code:%s", uid, e.msg, e.code)
        


def set_cookie(response, name, value, domain=None, path="/", expires=None):
    """Generates and signs a cookie for the give name/value"""
    timestamp = str(int(time.time()))
    value = base64.b64encode(value)
    signature = _cookie_signature(value, timestamp)
    signed_value = "|".join([value, timestamp, signature])
    cookie = Cookie.BaseCookie()
    cookie[name] = signed_value
    cookie[name]["path"] = path
    if domain: cookie[name]["domain"] = domain
    if expires:
        cookie[name]["expires"] = email.utils.formatdate(expires, localtime=False, usegmt=True)
    response["Set-Cookie"] = cookie.output()[12:]

def parse_cookie(value):
    """Parses and verifies a cookie value from set_cookie"""
    if not value: return None
    parts = value.split("|")
    if len(parts) != 3: return None
    if _cookie_signature(parts[0], parts[1]) != parts[2]:
        logger.warning("Invalid cookie signature %r", value)
        return None
    timestamp = int(parts[1])
    if timestamp < time.time() - 30 * 86400:
        logger.warning("Expired cookie %r", value)
        return None
    try:
        ret_val = base64.b64decode(parts[0]).strip()
        if len(ret_val) == 0:
            return None
        return ret_val
    except:
        return None


def _cookie_signature(*parts):
    """Generates a cookie signature.

    We use the Facebook app secret since it is different for every app (so
    people using this example don't accidentally all use the same secret).
    """
    hash = hmac.new(config.FACEBOOK_APP_SECRET, digestmod=hashlib.sha1)
    for part in parts: hash.update(part)
    return hash.hexdigest()
