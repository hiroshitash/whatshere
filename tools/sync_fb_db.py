'''
Created on Jun 9, 2012

@author: hiroshitashiro
'''
import sys
import logging

import wh_facebook as whfb
import mongo_persistence_layer as mpl

logger = logging.getLogger(__name__)


def main():
    logging.basicConfig()
    logger.setLevel(logging.DEBUG)
    
    persistence = mpl.MongoPersistenceLayer()
    fb =whfb.Facebook(persistence)
    
    if len(sys.argv) != 2:
        sys.stderr.write("Wrong argument. Need argument user or place")
        sys.exit(1) 
        
    if sys.argv[1] == "user":
        users = persistence.find_records('user', {'access_token': {"$exists": True}}, {'name': 1, 'access_token': 1})
        for user in users:
            print user
            fb.query_fb_and_save(user['access_token'])

    elif sys.argv[1] == "place":
        fb.sync_place_db()

    elif sys.argv[1] == "access_token":
        fb.sync_user_access_token()

    else:
        sys.stderr.write("Wrong argument. Need argument user or place")


if __name__ == '__main__':
    main()
