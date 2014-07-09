import  django.utils.simplejson as json

import logging
import urllib2

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

access_token = "AAAAAAITEghMBAPFhhmEKMhvGuTNewXNZBozzQvPr5zlwOeqZByJlC5rIjBqx5i9eRewqo44YhFiJBKNyGmXOdjvVYnfG0xenKqQdax7x4KkghgqYJN"

def main():
    try:
        # save user's likes                                                                                                                                                                                      
        likes_url = "https://graph.facebook.com/me/likes?access_token=%s" % access_token
        f = urllib2.urlopen(likes_url)
        likes_result_json = json.loads(f.read())
        logger.debug("\nlikes_result_json: %s" % likes_result_json)
        flag = True

        while flag:
            for like in likes_result_json.get('data', []):
                logger.info("name:%s, id:%s, category:%s" % (like.get('name', None), like.get('id', None), like.get('category', None)))
            next_page = likes_result_json.get('paging', []).get('next', None)
            logger.debug("next_page:%s" % next_page)

            flag = False
            if next_page is not None:
                flag = True
                f = urllib2.urlopen(next_page)
                likes_result_json = json.loads(f.read())
    except urllib2.HTTPError, e:
        #import pdb; pdb.set_trace()
        logger.error("%s. Possibly expired access token. error code:%s" % (e.msg, e.code))

if __name__ == "__main__":
    main()
