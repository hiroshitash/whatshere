import logging
import sys
import urllib2

import django.utils.simplejson as json

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

def get_geo_from_ip(ip):

    query_url = "http://www.datasciencetoolkit.org/ip2coordinates/%s" % (ip)
    logger.debug("\nquery_url: %s" % query_url)
    
    f = urllib2.urlopen(query_url)
    query_result_json = json.loads(f.read())
    logger.info("\nquery_result_json: %s" % query_result_json)
#    page = query_result_json.get('paging', None)
#    data = query_result_json.get('data', None)

#    print "page: %s" % page
#    if data is not None:
#        for p in data:
#            print p
    

if __name__ == "__main__":
    assert(len(sys.argv) > 1)
    get_geo_from_ip(sys.argv[1])
