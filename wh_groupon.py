import logging
import urllib
import urllib2

from django.http import HttpResponse, HttpResponseRedirect
import django.utils.simplejson as json

import config
import util

logger = logging.getLogger(__name__)

def get_groupon_deals(lat, lng, radius=100):
    groupon_query_url = "http://api.groupon.com/v2/deals?client_id=%s&lat=%s&lng=%s&radius=%s&sort=distance" % \
        (config.GROUPON_CLIENT_ID, lat, lng, radius)
    logger.debug("groupon_query_url: %s", groupon_query_url)
    try:
        f = urllib2.urlopen(groupon_query_url)
        response_json = json.loads(f.read())
    except urllib2.HTTPError as e:
        msg = e.fp.fp._sock.msg.dict['www-authenticate']
        logger.warn("Getting groupon deals failed. %s", msg)

#    
    for idx,val in enumerate(response_json.get('deals',[])):
        if isinstance(val.get('highlightsHtml', None), unicode):
            response_json['deals'][idx]['highlightsHtml'] = val['highlightsHtml'].encode('utf-8').replace("'", '').replace('"', '')
        #import pdb; pdb.set_trace()
        response_json['deals'][idx]['cjUrl'] = "%s?%s" % (config.COMISSION_JUNCTION_REDIRECT_URL, urllib.urlencode({'url':response_json['deals'][idx]['dealUrl']}))
    return response_json
