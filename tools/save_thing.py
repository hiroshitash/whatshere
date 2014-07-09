'''
Created on Jun 9, 2012

@author: hiroshitashiro
'''
import sys
import logging

import wh_facebook as whfb
import mongo_persistence_layer as mpl

logger = logging.getLogger(__name__)

# Mongodb data type:
#  Double 1
#  String 2
#  Object 3
#  Array 4
#  Binary data 5
#  Object id 7
#  Boolean 8
#  Date 9
#  Null 10
#  Regular expression 11
#  JavaScript code 13
#  Symbol 14
#  JavaScript code with scope 15
#  32-bit integer 16
#  Timestamp 17
#  64-bit integer 18
#  Min key 255
#  Max key 127

_map_dtype_did = {'long':1, 'str':2, 'obj':3, 'array':4, 'bdata':5, 'objectid':7,
                  'boolean':8, 'date':9, 'null':10, 'rexpr':11, 'javascript':15,
                  'int32':16, 'timestamp':17, 'int64':18, 'minkey':255, 'maxkey':127}

def main():
    logging.basicConfig()
    logger.setLevel(logging.DEBUG)
    
    persistence = mpl.MongoPersistenceLayer()
    fb =whfb.Facebook(persistence)
    

    collection_name = 'place'

    thing = {u'pic': u'https://fbcdn-profile-a.akamaihd.net/hprofile-ak-snc4/373118_100165354730_477883622_s.jpg', u'pic_small': u'https://fbcdn-profile-a.akamaihd.net/hprofile-ak-snc4/373118_100165354730_477883622_t.jpg', u'parking': {u'street': 0, u'lot': 1, u'valet': 0}, u'general_info': u'DISCLAIMER\n\nuShaka Marine World ("uShaka"), does not encourage or support the submission of any comments, information, photos, videos, links or other content ("Third Party Content") to the uShaka Brand Page ("Page") which infringes the rights of any third party, violates any law or other legal authority, is false and/or misleading in any manner or which fails to comply with Facebook\'s Terms and Conditions. By viewing the Page, you acknowledge that any content uploaded by anyone other than uShaka is the creation/views/responsibility of the submitter, and not uShaka. Notwithstanding, uShaka reserves the right, but assumes no obligation, to remove any Third Party Content in its sole discretion. Submission of any Third Party Content grants uShaka and its agents an unlimited, worldwide, perpetual, license and right to publish, use, publicly perform such content, or any idea contained therein, or any portion thereof, in any way, in any and all media now known or hereinafter developed, without territorial time or other limitation, for commercial, advertising/promotional or any other purposes, without consideration to the submitter. The uShaka Facebook team reserves the right to remove comments that don\u2019t abide by this policy. If an individual repeatedly violates this policy, that user will be blocked from posting in the future. uShaka claims no liability in any way connected to the use of or access to this uShaka Facebook page or any social \u201cLike\u201d objects created by uShaka. uShaka reserves the right to adopt additional terms or rules and to change or modify these terms or rules at any time.\n\n\xa9 2012 uShaka Marine World. All Rights Reserved. ', u'checkin_count': 17532, u'loc': [31.045499752895999, -29.867940027694999], u'payment_options': {u'amex': 0, u'cash_only': 0, u'visa': 0, u'mastercard': 0, u'discover': 0}, u'fan_count': 47436, u'location': {u'city': u'Durban', u'zip': u'4001', u'country': u'South Africa', u'longitude': 31.045514043988, u'state': u'', u'street': u'1 Bell Street', u'latitude': -29.868109084223999}, u'attire': None, u'latitude': -29.867940027694999, u'page_id': 100165354730L, u'website': u'http://www.ushakamarineworld.co.za http://www.twitter.com/ushakamarine', u'culinary_team': u'', u'description': u"SEA WORLD\nLocated in the centre of uShaka Marine World is Sea World, comprising a saltwater aquarium with indoor and outdoor displays and exhibits, the iconic cargo ship wreck, the 1200 seater dolphin stadium where you\u2019ll be entertained by the world-famous Gambit and friends, the seal stadium and penguin rookery. In addition to this, Sea World offers daily edutainment tours behind the scenes and special interactive activities such as snorkeling through the coral reefs and grottos and dive tank. \n\n\nWET 'n WILD\nA fun fresh water world of slides and pools, uShaka's Wet 'n Wild caters for the adrenaline junkie and those less adventurous! This freshwater entertainment facility offers thrilling water rides, swimming pools, and other leisure amenities. Its built for adrenaline pumping action and part of it actually flows through the uShaka ship wreck.\n\n\nVILLAGE WALK\nThe Village Walk is market-like, lively and characteristically Durban. The various structures will give the impression of a village, with articulated shop frontages and interdependent roofs, yet interlinked within. Restaurants, bars and shops enjoy exceptional views of uShaka and the Indian Ocean.\n\n\nUSHAKA KIDS WORLD\nuShaka Kids World has been designed with kids in mind; a place where children truly have the freedom to play! Alongside the ever popular Sea World, uShaka Kids World is a haven for kids from the ages of 2yrs to 10yrs, designed with jam-packed activities and interactive areas. Boasting Africa\u2019s biggest jungle gym, to Crabby Beach (giant sandpit) to Polly\u2019s Paint Pen (painting paradise), and for our movie stars, Cast-Aways (show time stage area) it\u2019s fun from sun-up to sun-down!", u'hours': [], u'phone': u'+27 (0)31 328 8000', u'price_range': None, u'categories': [{u'id': 148932728496725L, u'name': u'Public Places & Attractions'}, {u'id': 135093679891459L, u'name': u'Zoo/Aquarium'}, {u'id': 174777552574651L, u'name': u'Water Park'}], u'name': u'uShaka Marine World', u'type': u'ATTRACTIONS/THINGS TO DO', u'public_transit': u'', u'longitude': 31.045499752895999, u'display_subtext': u'Public Places & Attractions\u30fb51,355 were here', u'_id': u'100165354730'}

    # $ne not supported for $type so we go through one by one
    #things = persistence.find_records(collection_name, {'_id': {"$type": {"$ne": 7}}})
    id_dtype = persistence.get_id_datatype(collection_name)

    import pdb; pdb.set_trace()
    
    print thing
    persistence.remove_no_cast(collection_name, {'_id': thing['_id']})
    persistence.save(collection_name, thing)



if __name__ == '__main__':
    main()
