from abc import abstractmethod
#import exceptions
import datetime
import logging
import sys
import util

import pymongo
from pymongo import Connection
from bson.son import SON
from bson.objectid import ObjectId

import config
import constant
DEBUG = True
logger = logging.getLogger(__name__)

__all__ = ['get_user', 'save_list_objects', 'get_close_places', 'get_recommendation', 'trigger_fill_coll_preference']


class PersistenceLayerException (Exception):
    pass

class PersistenceLayer(object):
    @abstractmethod
    def connect(self):
        pass
    
    @abstractmethod
    def get_user(self, uid):
        pass
    
    @abstractmethod
    def save(self, collection_name, obj):
        pass
    
    @abstractmethod
    def save_list_objects(self, collection_name, objs):
        pass
    
    @abstractmethod 
    def find_records(self, collection_name, filter_arg={}, column=None, limit_num=None):
        pass
    
    @abstractmethod
    def get_close_places(self, uid, client_longitude, client_latitude):
        pass
    
    @abstractmethod
    def get_recommendation(self, uid, client_longitude, client_latitude):
        pass
    
    @abstractmethod
    def trigger_fill_coll_preference(self, uid, friend_uid_list):
        pass
    


_map_coll_id_dtype = {'user': 'long', 'place': 'long', 'checkin': 'str',
                      'preference': 'str', 'access_token': 'str',
                      'like': 'long', 'place_similar': 'long'}

class MongoPersistenceLayer(PersistenceLayer):
    
    _instance = None
    _connection = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(MongoPersistenceLayer, cls).__new__(
                                cls, *args, **kwargs)
        return cls._instance
    
    def __init__(self):
        self.connect()
    
    def connect(self):
        if MongoPersistenceLayer._connection is None:
            # Establish connection to mongodb
            try:
                #connection = Connection(config.URL_MONGODB, config.PORT_MONGODB)
                #logger.debug("connection:%s" % connection)
                self._connection = Connection(config.URL_MONGODB, config.PORT_MONGODB)[config.DB_NAME_MONGODB]
                logger.debug("self._connection:%s" % self._connection)
    
                self.USER = self._connection.user
                self.PLACE = self._connection.place
                self.CHECKIN = self._connection.checkin
                self.PREFERENCE = self._connection.preference
                self.ACCESS_TOKEN = self._connection.access_token
                self.LIKE = self._connection.like
                self.PLACE_SIMILAR = self._connection.place_similar
                self._map_collname_obj = {'user': self.USER, 'place': self.PLACE, 'checkin': self.CHECKIN,
                                           'preference': self.PREFERENCE, 'access_token': self.ACCESS_TOKEN,
                                           'like': self.LIKE, 'place_similar': self.PLACE_SIMILAR}
            except:
                import traceback
                logger.error("Connecting to mongodb failed..")
                logger.error("Unexpected error:%s", sys.exc_info()[0])
                logger.error("%s", traceback.format_exc())
                if DEBUG:
                    raise

    def get_connection(self):
        self.connect()
        return self._connection
    
    def _get_collection_obj(self, collection_name):
        #import pdb; pdb.set_trace()
        coll_obj = self._map_collname_obj.get(collection_name, None)
        if coll_obj is not None:
            return coll_obj
        else:
            raise PersistenceLayerException("collection %s not found." % collection_name)

    def get_user(self, uid):
        logger.debug("method get_user(uid: %s)" % (uid))
        try:
            return self.USER.find_one({"_id": long(uid)})
        except:
            msg = "Getting user for uid %s from mongodb failed.." % uid
            logger.warn(msg)
            logger.warn("%s", sys.exc_info())
            if DEBUG:
                raise PersistenceLayerException(msg)
            return None


    def cast_id(self, collection_name, target_id):
        dtype = self.get_id_datatype(collection_name)
        if dtype is None:
            raise PersistenceLayerException("_id datatype for collection %s not found.", collection_name)
        elif dtype == 'long':
            return long(target_id)
        elif dtype == 'str':
            return str(target_id)
        elif dtype == 'objectid':
            return ObjectId(target_id)
        else:
            raise PersistenceLayerException("unsupported datatype %s.", dtype)


    def get_id_datatype(self, collection_name):
        return _map_coll_id_dtype.get(collection_name, None)


    def find_records(self, collection_name, filter_arg={}, column=None, limit_num=None):
        if filter_arg.get('_id', None) is not None and not isinstance(filter_arg['_id'], dict) and \
            not isinstance(filter_arg['_id'], list):
            filter_arg['_id'] = self.cast_id(collection_name, filter_arg['_id'])

        coll_obj = self._get_collection_obj(collection_name)
        if limit_num is None:
            return coll_obj.find(filter_arg, column)
        else:
            return coll_obj.find(filter_arg, column).limit(int(limit_num))
        
        
    def find_one_record(self, collection_name, filter_arg={}, column=None):
        if filter_arg.get('_id', None) is not None and not isinstance(filter_arg['_id'], dict) and \
            not isinstance(filter_arg['_id'], list):
            filter_arg['_id'] = self.cast_id(collection_name, filter_arg['_id'])

        coll_obj = self._get_collection_obj(collection_name)
        return coll_obj.find_one(filter_arg, column)

        
    def update(self, collection_name, filter_arg, set_arg, upsert=False, multi=False):
        if filter_arg.get('_id', None) is not None:
            filter_arg['_id'] = self.cast_id(collection_name, filter_arg['_id'])

        if set_arg.get('_id', None) is not None:
            set_arg['_id'] = self.cast_id(collection_name, set_arg['_id'])

        coll_obj = self._get_collection_obj(collection_name)
        try:
            coll_obj.update(filter_arg, set_arg, upsert, multi)
        except:
            import traceback
            msg = "Updating collection %s filter %s set %s to mongodb failed.." % (collection_name, filter_arg, set_arg)
            logger.error(msg)
            logger.error("Unexpected error:%s", sys.exc_info())
            logger.error("%s", traceback.format_exc())
            if DEBUG:
                raise PersistenceLayerException(msg)


    def remove(self, collection_name, filter_arg):
        if filter_arg.get('_id', None) is not None and not isinstance(filter_arg['_id'], dict) and \
            not isinstance(filter_arg['_id'], list):
            filter_arg['_id'] = self.cast_id(collection_name, filter_arg['_id'])

        coll_obj = self._get_collection_obj(collection_name)
        try:
            coll_obj.remove(filter_arg)
        except:
            import traceback
            msg = "Removing collection %s filter %s to mongodb failed.." % (collection_name, filter_arg)
            logger.error(msg)
            logger.error("Unexpected error:%s", sys.exc_info())
            logger.error("%s", traceback.format_exc())
            if DEBUG:
                raise PersistenceLayerException(msg)

    def remove_no_cast(self, collection_name, filter_arg):
        coll_obj = self._get_collection_obj(collection_name)
        try:
            coll_obj.remove(filter_arg)
        except:
            import traceback
            msg = "Removing collection %s filter %s to mongodb failed.." % (collection_name, filter_arg)
            logger.error(msg)
            logger.error("Unexpected error:%s", sys.exc_info())
            logger.error("%s", traceback.format_exc())
            if DEBUG:
                raise PersistenceLayerException(msg)


    def save(self, collection_name, obj):
        if obj.get('_id', None) is not None:
            obj['_id'] = self.cast_id(collection_name, obj['_id'])

        #logger.debug("method save(collection_name:%s, obj:%s)" % (collection_name, obj))
        coll_obj = self._get_collection_obj(collection_name)
        
        try:
            coll_obj.save(obj)
        except:
            import traceback
            msg = "Saving %s objects %s to mongodb failed.." % (collection_name, obj)
            logger.error(msg)
            logger.error("Unexpected error:%s", sys.exc_info())
            logger.error("%s", traceback.format_exc())
            if DEBUG:
                raise PersistenceLayerException(msg)


    def save_list_objects(self, collection_name, objs):
        #logger.debug("method save_list_objects(collection_name:%s, objs:%s)" % (collection_name, objs))
        #logger.info("method save_list_objects()")

        try:
            for obj in objs:
                self.save(collection_name, obj)
        except:
            import traceback
            msg = "Saving %s objects %s to mongodb failed.." % (collection_name, objs)
            logger.error(msg)
            logger.error("Unexpected error:%s", sys.exc_info())
            logger.error("%s", traceback.format_exc())
            if DEBUG:
                raise PersistenceLayerException(msg)


    def get_general_close_places(self, client_longitude, client_latitude):
        #import pdb; pdb.set_trace()
        places = []
        try:
            client_longitude = float(client_longitude)
            client_latitude  = float(client_latitude)

            place_cursor = self.PLACE.find( { "loc" : {"$near": [client_longitude, client_latitude]} } ).limit(config.NUM_PLACES_FOR_LIST)

            for place in place_cursor:
                dist = util.calc_approximate_distance( (client_longitude, client_latitude), (place['longitude'], place['latitude']) )
                place['distance'] = dist
                place['distance_txt'] = "%.2f" % dist

                if place.get(u'description', None) is not None and len(place[u'description']) > 100:
                    place[u'description'] = "%s..." % place[u'description'][:100]
                if place.get('last_update', None) is not None:
                    del place['last_update']
                p_loc = place.get('location', {})
                place['address_url'] = "%s+%s+%s" % (p_loc.get('street', "").encode('utf-8').replace(' ', '+'), p_loc.get('city', "").encode('utf-8').replace(' ', '+'), p_loc.get('state',"").encode('utf-8').replace(' ', '+'))
                places.append(place)
        except:
            import traceback
            msg = "Getting close places from mongodb failed.."
            logger.error(msg)
            logger.error("Unexpected error:%s", sys.exc_info())
            logger.error("%s", traceback.format_exc())
            if DEBUG:
                raise PersistenceLayerException(msg)
            return []
        return places


    def get_close_places(self, uid, client_longitude, client_latitude, sort_by=constant.SORT_BY_DISTANCE):
        logger.debug("method get_close_places(\nuid:%s, \nclient_longitude:%s, \nclient_latitude:%s)" % (uid, client_longitude, client_latitude))
        try:
            client_longitude = float(client_longitude)
            client_latitude  = float(client_latitude)

            me_friend_id_list = self.USER.find_one({"_id": long(uid)}, {"friends": 1}).get("friends", [])
            me_friend_id_list.append(long(uid))
            logger.debug("friend_id_list: %s" % me_friend_id_list)

            friend_uname_cursor = self.USER.find({ "_id": {"$in": me_friend_id_list} }, {"name": 1})
            friend_uname_list = []
            for f in friend_uname_cursor:
                friend_uname_list.append(f['name'])
            #logger.debug("friend_uname_list: %s" % friend_uname_list)

            # Searching embedded documents hasn't been supported yet
            # checkin_list = USER.find( { "checkin.loc" : {"$near": [client_longitude, client_latitude]} }, {"checkin.loc": 1} ).limit(300)
            # alternative is making separate collection Checkin
            if sort_by==constant.SORT_BY_DISTANCE:
                checkin_cursor = self.CHECKIN.find( { "loc" : {"$near": [client_longitude, client_latitude]}, "author_uid": {"$in": me_friend_id_list} } ).limit(config.NUM_PLACES_FOR_LIST)
            else:
                checkin_cursor = self.CHECKIN.find( { "loc" : {"$near": [client_longitude, client_latitude]}, "author_uid": {"$in": me_friend_id_list} } ).limit(config.NUM_PLACES_FOR_LIST).sort("timestamp", pymongo.DESCENDING)

            checkin_target_id_list = []
            checkin_hash_target_id = {}
            checkin_display_hash_target_id = {}
            for cin in checkin_cursor:
                #logger.debug("cin: %s" % cin)
                cin["date"] = unicode(datetime.datetime.fromtimestamp(int(cin["timestamp"])).strftime('%m/%d/%Y'))  # to avoid not JSON serializable
                del cin["timestamp"]

                if checkin_hash_target_id.get(cin["target_id"], None) is None:
                    checkin_hash_target_id[cin["target_id"]] = [cin]
                    checkin_target_id_list.append(cin["target_id"])
                else:
                    checkin_hash_target_id[cin["target_id"]].append(cin)
                
                if checkin_display_hash_target_id.get(cin["target_id"], None) is None:
                    checkin_display_hash_target_id[cin["target_id"]] = ["%s (%s)" % (cin.get("uname", None), cin["date"])]
                else:
                    checkin_display_hash_target_id[cin["target_id"]].append("%s (%s)" % (cin.get("uname", None), cin["date"]))

            #logger.debug("checkin_list: %s" % checkin_list)
            #logger.debug("checkin_target_id_list: %s" % checkin_target_id_list)
            logger.debug("checkin_display_hash_target_id: %s" % checkin_display_hash_target_id)

            #import pdb; pdb.set_trace()
            places = {}
            #place_cursor = self.PLACE.find( { "loc" : {"$near": [client_longitude, client_latitude]}, "page_id" : {"$in": checkin_target_id_list} } )
            place_cursor = self.PLACE.find( { "page_id" : {"$in": checkin_target_id_list} } )
            for place in place_cursor:
                place["checkins"] = checkin_hash_target_id[place["page_id"]]
                place["checkin_display_txts"] = checkin_display_hash_target_id[place["page_id"]]

                dist = util.calc_approximate_distance( (client_longitude, client_latitude), (place['longitude'], place['latitude']) )
                place['distance'] = dist
                place['distance_txt'] = "%.2f" % dist

                if place.get(u'description', None) is not None and len(place[u'description']) > 100:
                    place[u'description'] = "%s..." % place[u'description'][:100]
                if place.get('last_update', None) is not None:
                    del place['last_update']
                p_loc = place.get('location', {})
                place['address_url'] = "%s+%s+%s" % (p_loc.get('street', "").encode('utf-8').replace(' ', '+'), p_loc.get('city', "").encode('utf-8').replace(' ', '+'), p_loc.get('state',"").encode('utf-8').replace(' ', '+'))
                places[place['page_id']] = place

            places_ordered = []
            for target_id in checkin_target_id_list:
                if places.get(target_id, None) is not None:
                    places_ordered.append(places[target_id])
                    logger.debug("ordered close place\n: %s" % places[target_id])
            num_places = len(places_ordered)
            logger.debug("num of close places retrieved: %s" % num_places)
            return places_ordered
        except:
            import traceback
            msg = "Getting close places from mongodb failed.."
            logger.error(msg)
            logger.error("Unexpected error:%s", sys.exc_info())
            logger.error("%s", traceback.format_exc())
            if DEBUG:
                raise PersistenceLayerException(msg)
            return []


    def get_recommendation(self, uid, client_longitude, client_latitude):
#        import pdb; pdb.set_trace()
        client_longitude = float(client_longitude)
        client_latitude = float(client_latitude)
        logger.debug("uid:%s, client_longitude:%s, client_latitude:%s", uid, client_longitude, client_latitude)
        places_recommendation = []

        user = self.get_user(uid)
        friend_ids = user['friends']
        me_friend_ids = [uid] + friend_ids

        logger.debug("num of associated users: %s", len(me_friend_ids))
        #logger.debug("associated users: %s", me_friend_ids)
        me_friend_checkins = self.CHECKIN.find({"loc":{"$near": [client_longitude, client_latitude]}, "author_uid": {"$in": me_friend_ids}}, {'target_id':1}).limit(30)
        count = me_friend_checkins.count()

        # still 0 then we can't recommend any
        if count == 0:
            return []

        list_ci_target_ids = []
        for ci in me_friend_checkins:
            #logger.debug("%s", ci)
            #logger.debug("%s %s", ci.get('uname', None), ci.get('loc', None))
            list_ci_target_ids.append(long(ci['target_id']))
            
        similar_places_cursor = self.PLACE_SIMILAR.find({"loc":{"$near": [client_longitude, client_latitude]}, "source_page_ids": {"$in": list_ci_target_ids}},
                                                            {'_id':1, 'location':1, 'longitude':1, 'latitude':1, 'description':1, 'page_id':1, 'display_subtext':1, 
                                                             'name':1, 'loc':1, 'categories':1, 'page_url':1}
                                                            ).limit(config.NUM_PLACES_FOR_LIST)
        place_id_recomm_hash = {}
        for similar_place in similar_places_cursor:
            id_similar_place = similar_place.get('_id', None)
            if id_similar_place is not None and place_id_recomm_hash.get(long(id_similar_place), None) is None:
                place_id_recomm_hash[long(id_similar_place)] = True
                dist = util.calc_approximate_distance( (client_longitude, client_latitude), (similar_place['loc'][0], similar_place['loc'][1]) )
                similar_place['distance'] = dist
                similar_place['distance_txt'] = "%.2f" % dist

                if similar_place.get(u'description', None) is not None and len(similar_place[u'description']) > 100:
                    similar_place[u'description'] = "%s..." % similar_place[u'description'][:100]

                if similar_place.get('last_update', None) is not None:
                    del similar_place['last_update']

                places_recommendation.append(similar_place)
                logger.debug("recommend place\n: %s" % similar_place)

        #import pdb; pdb.set_trace()
        return places_recommendation


    def trigger_fill_coll_preference(self, uid, friend_uid_list):
        # user's checkins get rate 0.5                                                                                                                                                                                       
        my_rate_hash = {}
        my_checkin_cursor = self.CHECKIN.find( {"author_uid": uid},
                                               {"author_uid": 1, "target_id": 1, "timestamp": 1} ).sort("timestamp", -1)
        for cin in my_checkin_cursor:
            target_id = long(cin["target_id"])
            if my_rate_hash.get(target_id, None) is None:
                my_rate_hash[target_id] = {"rate": 0.5, "created_at": cin["timestamp"]}
        #import pdb; pdb.set_trace()
        logger.debug( "my_rate_hash %s", my_rate_hash )

        # friends' checkins get rate 0.3                                                                                                                                                                                     
        friend_rate_hash = {}
        friend_checkin_cursor = self.CHECKIN.find( {"author_uid": {"$in": friend_uid_list}},
                                                   {"author_uid": 1, "target_id": 1, "timestamp": 1} ).sort("timestamp", -1)
        for cin in friend_checkin_cursor:
            target_id = long(cin["target_id"])
            if friend_rate_hash.get(target_id, None) is None:
                friend_rate_hash[target_id] = {"rate": 0.3, "created_at": cin["timestamp"]}
            else:
                friend_rate_hash[target_id]["rate"] = friend_rate_hash[target_id]["rate"] + 0.3
                if friend_rate_hash[target_id]["rate"] > 1.0:
                    friend_rate_hash[target_id]["rate"] = 1.0
                friend_rate_hash[target_id]["created_at"] = cin["timestamp"]
        logger.debug( "friend_rate_hash %s" % friend_rate_hash )

        rate_hash = friend_rate_hash
        for target_id, my_rate_item in my_rate_hash.iteritems():
            #import pdb; pdb.set_trace()
            if rate_hash.get(target_id, None) is None:
                rate_hash[target_id] = {"rate": my_rate_item["rate"], "created_at": my_rate_item["created_at"]}
            else:
                rate_hash[target_id]["rate"] = rate_hash[target_id]["rate"] + my_rate_item["rate"]
                if rate_hash[target_id]["rate"] > 1.0:
                    rate_hash[target_id]["rate"] = 1.0

        rate_list = []
        for target_id, rate_item in rate_hash.iteritems():
            rate_list.append({"_id" : "%s_%s" % (uid, target_id), "uid": long(uid), "page_id": long(target_id),
                              "rate": rate_item['rate'],
                              "created_at": rate_hash[target_id]["created_at"]})
        logger.debug( "rate_list %s" % rate_list )
        self.save_list_objects('preference', rate_list)
        return rate_list

    
    def is_similar_places_saved(self, place_page_id):
        #import pdb; pdb.set_trace()
        similar_place_dict = self.PLACE_SIMILAR.find_one({"source_page_ids": {"$in": [place_page_id]}}, {'_id':1} )
        return similar_place_dict is not None and len(similar_place_dict) > 0

    
    def save_similar_places(self, places, source_page_id):
        for p in places:
            self.save_similar_place(p, source_page_id)


    def save_similar_place(self, place, source_page_id):
        source_page_id = long(source_page_id)
        if long(place.get('page_id', -1)) == long(source_page_id):
            return
            
        place_orig = self.find_one_record('place_similar', {'_id': place['page_id']})
        if place_orig is not None:
            list_source_page_ids = place_orig.get('source_page_ids')
            if not (source_page_id in list_source_page_ids):
                list_source_page_ids.append(source_page_id)
        else:
            list_source_page_ids = [source_page_id]
        
        place['_id'] = place['page_id']
        place['source_page_ids'] = list_source_page_ids
        self.save('place_similar', place)


    def remove_old_page_id(self, page_id):
        try:
            #import pdb; pdb.set_trace()
            self.remove('checkin', {"page_id": long(page_id)})
            self.remove('place', {"page_id": long(page_id)})
            self.remove('place_similar', {"page_id": long(page_id)})
            # source_page_ids will be cleaned when periodic save is run
            # self.remove('place_similar', {"sourcepage_ids": $in long(page_id)})
            self.remove('preference', {"page_id": long(page_id)})
        except:
            util.log_exception_error(logger, "Unexpected error at remove_old_page_id(%s) failed." % page_id)
            raise

        
