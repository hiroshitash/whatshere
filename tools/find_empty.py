'''
Created on Jun 9, 2012

@author: hiroshitashiro
'''
import sys
import logging
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

    # $ne not supported for $type so we go through one by one
    #things = persistence.find_records(collection_name, {'_id': {"$type": {"$ne": 7}}})
    #id_dtype = persistence.get_id_datatype(collection_name)

    import pdb; pdb.set_trace()
    empty = persistence.get_user(1)
    print empty



if __name__ == '__main__':
    main()
