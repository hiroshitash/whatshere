'''
Created on Jun 9, 2012

@author: hiroshitashiro
'''
import sys
import logging

#import wh_facebook as whfb
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
    #fb =whfb.Facebook(persistence)
    
    if len(sys.argv) < 2:
        sys.stderr.write("Wrong argument. Need arguments for <func>, <collection name> etc.")
        sys.exit(1) 

        
    if sys.argv[1] == "pkey":
        collection_name = sys.argv[2]

        # $ne not supported for $type so we go through one by one
        #things = persistence.find_records(collection_name, {'_id': {"$type": {"$ne": 7}}})
        id_dtype = persistence.get_id_datatype(collection_name)

        if id_dtype == 'objectid':
            sys.stderr.write("Datatype objectid not supported. Collection: %s", collection_name)
            return

        if id_dtype == 'long':
            things = persistence.find_records(collection_name, {'_id': {"$type": _map_dtype_did['str']}})
        elif id_dtype == 'str':
            things = persistence.find_records(collection_name, {'_id': {"$type": _map_dtype_did['long']}})

        #import pdb; pdb.set_trace()
        for thing in things:
            print thing
            persistence.remove_no_cast(collection_name, {'_id': thing['_id']})
            persistence.save(collection_name, thing)
            
    elif sys.argv[1] == "rate":
        '''
        things = persistence.find_records('preference', {'rate': {"$type": 3}})
        for thing in things:
            print thing
            print thing.get('rate').get('rate')
            print thing.get('rate').get('created_at')
            persistence.update('preference', {'_id':thing['_id']}, 
                               {"$set": {'rate': thing.get('rate').get('rate')}})
        '''
        users = persistence.find_records('user', {'access_token': {"$exists": True}}, {'_id': 1, 'friends': 1})
        for user in users:
            #import pdb; pdb.set_trace()
            persistence.trigger_fill_coll_preference(user['_id'], user['friends'])                        

    else:
        sys.stderr.write("Wrong argument. Need arguments for <func>, <collection name> etc")


if __name__ == '__main__':
    main()
