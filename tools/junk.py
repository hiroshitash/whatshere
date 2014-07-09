'''
Created on Jul 6, 2012

@author: hiroshitashiro
'''

#
#
# This version saves collection User with embedded Checkins. However, mongodb doesn't support searching embedded docs so we will 
# have to wait using this until they support the search.
#    def query_fb_and_save(self, access_token):
#        logger.info("query_fb start")
#
#        fql_queries =  '{"me_query"      : "SELECT uid, name FROM user WHERE uid = me()",'
#        fql_queries += '"friend_query"   : "SELECT uid2 FROM friend WHERE uid1 = me()",'
#        fql_queries += '"fname_query"    : "SELECT uid, name FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE uid1 = me())",'
#        fql_queries += '"my_checkin_query"      : "SELECT page_id, author_uid, coords, tagged_uids, message, timestamp FROM checkin WHERE author_uid = me() order by ti#mestamp",'
#        fql_queries += '"friend_checkin_query"  : "SELECT page_id, author_uid, coords, tagged_uids, message, timestamp FROM checkin WHERE author_uid IN '
#        fql_queries +=                             '(SELECT uid2 FROM friend WHERE uid1 = me()) order by author_uid",'
#        fql_queries += '"page_query"     : "SELECT page_id, pic_small, pic, fan_count, type, website, general_info, location, parking, hours, public_transit, attire, '
#        fql_queries +=                      'payment_options, price_range, phone, culinary_team FROM page WHERE page_id IN '
#        fql_queries +=                      '(SELECT page_id FROM checkin WHERE author_uid = me() OR author_uid IN (SELECT uid2 FROM friend WHERE uid1 = me())) order b#y page_id",'
#        fql_queries += '"location_query" : "SELECT page_id, name, description, longitude, latitude, checkin_count, display_subtext '
#        fql_queries +=                      'FROM place WHERE page_id IN '
#        fql_queries +=                      '(SELECT page_id FROM checkin WHERE author_uid = me() OR author_uid IN '
#        fql_queries +=                      ' (SELECT uid2 FROM friend WHERE uid1 = me())) order by page_id",'
#        fql_queries += '}'
#    
#        fql_queries = urllib.quote_plus(fql_queries)
#        fql_queries_url = "https://api.facebook.com/method/fql.multiquery?access_token=%s&queries=%s&format=json" % (access_token, fql_queries)
#
#        logger.info("\nfql_queries_url: %s" % fql_queries_url)
#
#
#        f = urllib2.urlopen(fql_queries_url)
#        fql_result_json = json.loads(f.read())
#        logger.debug("\nfql_result_json: %s" % fql_result_json)
#
#        me_elem              = None
#        friend_list          = None
#        fname_list           = None
#        my_checkin_list      = None
#        friend_checkin_list  = None
#        page_list            = None
#        location_list        = None
#        for elem in fql_result_json:
#            if elem.get('name') == 'me_query':
#                me_elem = elem.get('fql_result_set')[0]
#            elif elem.get('name') == 'friend_query':
#                friend_list = elem.get('fql_result_set')
#            elif elem.get('name') == 'fname_query':
#                fname_list = elem.get('fql_result_set')
#            elif elem.get('name') == 'my_checkin_query':
#                my_checkin_list = elem.get('fql_result_set')
#            elif elem.get('name') == 'friend_checkin_query':
#                friend_checkin_list = elem.get('fql_result_set')
#            elif elem.get('name') == 'page_query':
#                page_list = elem.get('fql_result_set')
#            elif elem.get('name') == 'location_query':
#                location_list = elem.get('fql_result_set')
#
#        #logger.info("\n\nme_elem: %s" % me_elem)
#        logger.debug("\n\nfriend_list: %s" % friend_list)
#        logger.info("\n\nfname_list: %s" % fname_list)
#        #logger.info("\n\ncheckin_list: %s" % checkin_list)
#        #logger.info("\n\npage_list: %s" % page_list)
#
#        # construct friend id list
#        friend_id_list = []
#        for frnd in friend_list:
#            friend_id_list.append(frnd['uid2'])
#        logger.debug("\n\nfriend_id_list: %s" % friend_id_list)
#
#        # save user me
#        logger.debug("self.access_token:%s, me_elem:%s, self.query_string:%s" % (self.access_token, me_elem, self.query_string))
#        wmongo.save_list_objects([{"_id":long(me_elem['uid']), "name":me_elem['name'], "access_token":self.access_token, "friends":friend_id_list, "checkin":my_checkin#_list, "query_string":self.query_string}], wmongo.USER)
#
#        
#        # construct friend user list
#        fcheckin_hash = {}
#        for checkin in friend_checkin_list:
#            if checkin.get("coords",None) != None and checkin["coords"]["longitude"] != None and checkin["coords"]["latitude"] != None:
#                checkin["loc"] = [checkin["coords"]["longitude"], checkin["coords"]["latitude"]]
#                del checkin["coords"]
#
#            if fcheckin_hash.has_key("%s" % checkin['author_uid']):
#                fcheckin_hash["%s" % checkin['author_uid']].append(checkin)
#            else:
#                fcheckin_hash["%s" % checkin['author_uid']] = [checkin]
#        logger.info("\n\nfcheckin_hash: %s" % fcheckin_hash)
#
#        fname_hash = {}
#        for fname in fname_list:
#            fname_hash["%s" % fname['uid']] = fname['name']
#
#        logger.debug("\n\nfname_hash: %s" % fname_hash)
#        #logger.debug("\n\nfname_hash[1775744666]: %s" % (fname_hash[1775744666]))
#        # save friend users
#        for fid in friend_id_list:
#            logger.debug("fid: %s\n" % (fid))
#            logger.debug("fname_hash[%s]: %s\n" % (fid, fname_hash["%s" % fid]))
#            logger.debug("\n\nfcheckin_hash[%s]: %s" % (fid, fcheckin_hash[fid]))
#            wmongo.USER.update({"_id": long(fid)}, { "$set": {"name":fname_hash[fid], "checkin":fcheckin_hash[fid]} }, True)
#        #wmongo.save_list_objects(checkin_list, wmongo.CHECKIN)
#
#
#        # Merge page and place if same page_id
#        idx_page = 0
#        for place in location_list:
#            logger.info("\n\nplace: %s" % place)
#            place['_id'] = "%s" % (place['page_id'])
#            place['loc'] = [place['longitude'], place['latitude']]
#
#            while place['page_id'] > page_list[idx_page]['page_id']:
#                idx_page += 1
#            page = page_list[idx_page]
#
#            if place['page_id'] == page['page_id']:
#                place = dict(place.items() + page.items())
#
#        # save locations
#        logger.debug("\n\nlocation_list to be saved in mongodb: %s" % location_list)
#        wmongo.save_list_objects(location_list, wmongo.PLACE)
#        return me_elem['uid']
#