import logging

import mongo_persistence_layer as mpl
import wh_facebook as whfb

def main():
    persistence = mpl.MongoPersistenceLayer()
    fb = whfb.Facebook(persistence)
    
    #places_rec = persistence.get_recommendation(19704276, -84.432916454413, 33.640574980176)
    places_rec = persistence.get_recommendation(19704276, -122.4212314, 37.7633761)
    #places_rec = persistence.get_recommendation(549213884, -122.42211131, 37.764221663333)
    
    for p in places_rec:
        if isinstance(p, dict):
            print "Name:", p['name'], " categories:", p.get('categories'), " display_subtext", repr(p['display_subtext']), \
                " type:", p.get('type', None), " latitude:", p['latitude'], " longitude:", p['longitude'], \
                "checkin count:", p['checkin_count'], "fan count:", p['fan_count']
        else:
            import pdb; pdb.set_trace()

if __name__ == "__main__":
    main()
