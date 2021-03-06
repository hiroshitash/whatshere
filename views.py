import base64
from datetime import datetime
from datetime import timedelta
import logging
import string
import threading
import time
import urllib
import urllib2
import urlparse

from django.core.paginator import EmptyPage, InvalidPage
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
import django.utils.simplejson as json
from django.utils.decorators import classonlymethod
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, TemplateView, View

import config
import constant
import mongo_persistence_layer as mpl
import wh_groupon as whgo
import wh_facebook as whfb


NUM_PLACES_PER_PAGE = 20
DAY_IN_SECS = 60 * 60 * 24

SORT_BY_DISTANCE = 0
SORT_BY_CHECKIN_DATE = 1

logger = logging.getLogger(__name__)


class PlaceListViewBaseHandler(ListView):

    '''Given facebook access token, location info, it provides list of checkins or 
       place recommendation.

       Known issues:
       HttpResponseRedirect does not because it is fb canvas page. We have to use javascript
       redirect for workaround.
    '''
    def __init__(self, **kwds):
        super(PlaceListViewBaseHandler, self).__init__(**kwds)
        self.persistence = mpl.MongoPersistenceLayer()
        self.fb = whfb.Facebook(self.persistence)

    def handle_iphone_access_token(self):
        logger.debug("from iphone")
        #import pdb; pdb.set_trace()
        self.access_token = self.request.POST.get('access_token', None) or self.request.GET.get('access_token', None) 
        if self.access_token is None:
            return HttpResponse(json.dumps(''), mimetype='application/json')

        # TODO
        # get self.access_token_expirea and self.user_id like handle_fb_canvas_access_token do
        self.user = self.persistence.find_one_record('user', {'access_token':self.access_token})
        self.uid = None
        self.access_token_expires = None
        if self.user is not None:
            self.uid = self.user.get('_id', None)
            self.access_token_expires = self.user.get('access_token_expires', 0)
        else:
            # Download the user profile and cache a local instance of the
            # basic profile info
            profile = json.load(urllib.urlopen(
                "https://graph.facebook.com/me?" +
                urllib.urlencode(dict(access_token=self.access_token))))

            current_user = self.persistence.get_user(profile['id'])
            if current_user is None:  # no record in db
                current_user = {}
            
            self.uid = profile['id']
            current_user[u'_id'] = profile['id']
            current_user[u'name'] = profile['name']
            current_user[u'link'] = profile['link']
            current_user[u'access_token'] = self.access_token

            try:
                current_user[u'access_token_expires'] = long(self.access_token_expires)
            except:
                current_user[u'access_token_expires'] = 0
            self.persistence.save('user', current_user)
        return None

    def get_coordinate(self):
        logger.debug("get_coordinate begins.")
        
        self.client_loc_longitude = self.request.POST.get('longitude', None) or self.request.GET.get('longitude', None)
        self.client_loc_latitude = self.request.POST.get('latitude', None) or self.request.GET.get('latitude', None)
        
        app_url = config.FACEBOOK_CANVAS_PAGE + '/'

        #if self.request.COOKIES.get("fb_user") is not None:
        if config.FLAG_INDIVIDUAL_WEBSITE:
            app_url = config.WEBSITE_HOST + '/view.py'

        logger.debug("app_url: %s" % app_url)
        if (self.client_loc_longitude is None or self.client_loc_latitude is None) and \
                self.request.GET.get('geobrowsertried', None) is None:
            count = self.request.GET.get('c', 0) + 1;
            return render_to_response('coordinate.tmpl', {'app_url': app_url, 'signed_request': self.signed_req,
                                                          'refresh_cnt': count, 'access_token': self.access_token})

        self.client_loc_country = None
        self.client_loc_state   = None
        self.client_loc_city    = None
        
        # find location based on client IP address
        if self.client_loc_longitude is None or self.client_loc_latitude is None:
            client_ip = self.request.META.get('REMOTE_ADDR', None)
            
            """
            geo_url = "http://api.hostip.info/get_html.php?ip=%s&position=true" % client_ip
            geo_str = urllib2.urlopen(geo_url).read()
            #logger.debug("geo_str: %s" % geo_str)
            import re
            pattern = re.compile(
                "Country:\s+(.*?)[\n\s]*City:[\n\s]*(.*?)[\n\s]*Latitude:\s+([-+]?\d+\.\d+)[\n\s]*Longitude:\s+([-+]?\d+\.\d+).*")
            m = pattern.match(geo_str)

            if m is None:
                logger.warn("Could not identify Geo from IP %s geo_str: %s, self.request.META:%s" % 
                            (client_ip, geo_str, self.request.META))
                self.client_loc_country = "UNITED STATES (US)"
                self.client_loc_city = "Saratoga, CA"
                self.client_loc_latitude = "37.2678"
                self.client_loc_longitude = "-122.023"
                logger.warn("Assigned Saratoga, CA for now.")
            else:
                self.client_loc_country = m.group(1)
                self.client_loc_city = m.group(2)
                self.client_loc_latitude = m.group(3)
                self.client_loc_longitude = m.group(4)
                logger.debug("client_ip:%s, country:%s, city:%s" % (client_ip, self.client_loc_country, self.client_loc_city))
            """

            try:
                geo_query_url = "http://www.datasciencetoolkit.org/ip2coordinates/%s" % (client_ip)
                logger.debug("geo_query_url: %s\n" % geo_query_url)
                f = urllib2.urlopen(geo_query_url)

                geo_query_result_json = json.loads(f.read()).get(client_ip)
                logger.info("geo_query_result_json: %s\n" % geo_query_result_json)

                self.client_loc_country = geo_query_result_json.get('country_name', None)
                self.client_loc_state = geo_query_result_json.get('region', None)
                self.client_loc_city = geo_query_result_json.get('locality', None)
                self.client_loc_latitude = geo_query_result_json.get('latitude', None)
                self.client_loc_longitude = geo_query_result_json.get('longitude', None)
            except Exception, e:
                logger.warn("Could not identify Geo for IP %s. %s" % (client_ip, e))
                self.client_loc_country = "UNITED STATES (US)"
                self.client_loc_state = "CA"
                self.client_loc_city = "Saratoga"
                self.client_loc_latitude = "37.2678"
                self.client_loc_longitude = "-122.023"
                logger.warn("Assigned Saratoga, CA for now.")

            logger.debug("client_loc_longitude:%s, client_loc_latitude:%s" % (self.client_loc_longitude, self.client_loc_latitude))
            return None

    def get_queryset(self):
        logger.debug("get_queryset start")

        if self.request.GET.get(u'wh_q') == u'recommend':
            self.flag_recommend = True
        else:
            self.flag_recommend = False

        try:
            self.sort_by = int(self.request.GET.get(u'sort_by', constant.SORT_BY_DISTANCE))
        except:
            self.sort_by = constant.SORT_BY_DISTANCE

        if self.sort_by != constant.SORT_BY_CHECKIN:
            self.sort_by = constant.SORT_BY_DISTANCE

        if self.uid is None:
            return []

        logger.info("self.uid:%s" % self.uid)
        #import pdb; pdb.set_trace()
        self.user = self.persistence.get_user(self.uid)

        #self.fb.query_fb_and_save(self.access_token, self.access_token_expires, self.client_loc_longitude, self.client_loc_latitude)
        # run fql queries agenst fb
        #if user == None or user.get("last_update", None) == None or datetime.now() - user["last_update"] > timedelta(hours=1):
        if self.user is None or self.user.get("last_update", None) is None or datetime.now() - self.user["last_update"] > timedelta(minutes=2):
            if self.request.GET.get(u'wh_q') != u'recommend' and self.request.GET.get(u'wh_q') != u'deal':
                # Query FB and update checkin info if production
                #if not config.dev:
                #import pdb; pdb.set_trace()
                logger.debug("Calling self.fb.query_fb_and_save in separate thread")
                t = threading.Thread(target=self.fb.query_fb_and_save,
                                 args=[self.access_token, self.access_token_expires, self.client_loc_longitude, self.client_loc_latitude],
                                 kwargs={})
                t.setDaemon(True)
                t.start()
            self.persistence.update('user', {"_id": self.uid}, 
                                    { "$set": {"access_token":self.access_token, "access_token_expire":self.access_token_expires} }, upsert=True)
        else:
            # just update access token and expires
            self.persistence.update('user', {"_id": self.uid}, 
                                    { "$set": {"access_token":self.access_token, "access_token_expire":self.access_token_expires} }, upsert=True)

        uid = None
        if self.user is not None:
            uid = self.user.get("_id", None)
        if uid == None:
            logger.error("Error getting user info.")
            return self.get_general_queryset()
        else:
            last_update = self.user.get("last_update", None)
            logger.debug("user last_update:%s type:%s" % (last_update, type(last_update)))
            logger.debug("now:%s" % datetime.now())
            assert(self.request.GET.get(u'wh_q') != u'deal')

            if self.flag_recommend:                
                return self.persistence.get_recommendation(uid, self.client_loc_longitude, self.client_loc_latitude)
            else:
                return self.persistence.get_close_places(uid, self.client_loc_longitude, self.client_loc_latitude, self.sort_by)

    def get_general_queryset(self):
        # get 
        return self.persistence.get_general_close_places(self.client_loc_longitude, self.client_loc_latitude)

    def post(self, request, **kwargs):
        #import pdb; pdb.set_trace()
        logger.debug("post start request: %s kwargs:%s" % (request, kwargs))
        logger.debug("http origin: %s" % (self.request.META.get('HTTP_ORIGIN', None)))
        logger.info("agent: %s" % request.META.get('HTTP_USER_AGENT', None))

        self.signed_req = self.request.POST.get('signed_request', None) or self.request.GET.get('signed_request', None)

        # handle_xxx_access_token will set up self.access_token, self.access_token_expires and self.uid        
        # access from iphone
        if self.request.POST.get('sdk', None) == 'ios':          
            handler = PlaceViewJSONHandler()
        # access from ajax, return only tab content
        elif request.GET.get('wh_format', False) == 'ajax' or request.GET.get(u'wh_format', False) == u'ajax':   
            handler = PlaceViewAJAXHandler()
        # access for individual website
        elif config.FLAG_INDIVIDUAL_WEBSITE:
            handler = PlaceViewIndividualSiteHandler()
        # access for fb canvas page
        else:                               
            handler = PlaceViewCanvasPageHandler()
        
        # initialize handler there must be a better way to do the same
        # passing self to constructor etc.
        handler.signed_req = self.signed_req
        handler.request = request
        handler.kwargs = kwargs
        return handler.post(request, **kwargs)

    def get(self, request, **kwargs):
        return self.post(request, **kwargs)


    #
    # For debugging purpose
    #
    @classonlymethod
    @csrf_exempt
    def as_view(self, **initkwargs):
#        logger.info("dir(super): %s", dir(super(PlaceListViewBaseHandler, self)))
#        logger.info("**initkwargs: %s", (initkwargs))
        return super(PlaceListViewBaseHandler, self).as_view(**initkwargs)


class PlaceViewJSONHandler(PlaceListViewBaseHandler):
    def post(self, request, **kwargs):
        logger.info("handle access_token for json request")
        redirect = self.handle_iphone_access_token()
        
        # redirect to permission or login page if access_token not found
        if redirect is not None:
            return redirect
        
        # extend access token if expiring within a day
        self.access_token, self.access_token_expires = self.fb.get_extended_access_token_w_timeout(self.access_token, self.access_token_expires, DAY_IN_SECS)
        logger.debug("access_token: %s, expires:%s", self.access_token, self.access_token_expires)
        
        self.get_coordinate()
        place_list = self.get_queryset()
        return HttpResponse(json.dumps(place_list), mimetype='application/json')
        

class PlaceViewAJAXHandler(PlaceListViewBaseHandler):
    def deals_response(self, request, kwargs, template_name):
        logger.info("handle deals_response for ajax request")
        redirect = self.get_coordinate()

        try:
            page_num = int(request.GET.get('page', '1'))
        except ValueError:
            page_num = 1

        deals_json = whgo.get_groupon_deals(self.client_loc_latitude, self.client_loc_longitude)

        return render_to_response(template_name, 
                                  {'deal_list': deals_json.get('deals', []), 
                                   'pagination': deals_json.get('pagination', None)})

    def post(self, request, **kwargs):
        logger.info("handle access_token for ajax request")

        redirect = self.handle_iphone_access_token()
        # redirect to permission or login page if access_token not found
        if redirect is not None:
            return redirect

        if is_mobile(request):
            template_dir = 'm'
        else:
            template_dir = 'w'

        if self.request.GET.get(u'wh_q') == u'recommend':
            template_name = '%s/recommendation_tab.tmpl' % template_dir
        elif self.request.GET.get(u'wh_q') == u'deal':
            template_name = '%s/deal_tab.tmpl' % template_dir
            return self.deals_response(request, kwargs, template_name)
        else:
            template_name = '%s/checkin_tab.tmpl' % template_dir

        # extend access token if expiring within a day
        self.access_token, self.access_token_expires = self.fb.get_extended_access_token_w_timeout(self.access_token, self.access_token_expires, DAY_IN_SECS)
        logger.debug("access_token: %s, expires:%s", self.access_token, self.access_token_expires)

        redirect = self.get_coordinate()
        
        place_list = self.get_queryset()
        #import pdb; pdb.set_trace()
        if self.user is None or len(place_list) == 0:
            flag_first_time = True
            place_list = self.get_general_queryset()
        else:
            flag_first_time = False

        #import pdb; pdb.set_trace()
        location_paginator, page, page.object_list, is_paginated = self.paginate_queryset(place_list, kwargs['paginate_by'])
        # Make sure page request is an int. If not, deliver first page.
        try:
            page_num = int(request.GET.get('page', '1'))
        except ValueError:
            page_num = 1

        # If page request (9999) is out of range, deliver last page of results.
        try:
            page = location_paginator.page(page_num)
        except (EmptyPage, InvalidPage):
            page = location_paginator.page(location_paginator.num_pages)

        places = page.object_list
        recommend_list = []
        checkin_list = []
        if self.flag_recommend or flag_first_time:
            recommend_list = places
            if flag_first_time:
                tab_num = 0
            else:
                tab_num = 1
        else:
            checkin_list = places
            tab_num = 0
            #import pdb; pdb.set_trace()
        return render_to_response(template_name,
                    {'checkin_list': checkin_list, 'recommend_list': recommend_list, 
                     'app_url': config.FACEBOOK_CANVAS_PAGE, 'agent': request.META.get('HTTP_USER_AGENT', None),
                     'client_country': self.client_loc_country, 'client_state': self.client_loc_state, 
                     'client_city': self.client_loc_city, 
                     'flag_geobrowsertried': request.GET.get('geobrowsertried', False),
                     'client_lat': self.client_loc_latitude, 'client_long': self.client_loc_longitude,
                     'ec2_page': config.EC2_APP_PAGE, 'access_token': self.access_token, 
                     'is_paginated': is_paginated, 'page': page, 'paginator': location_paginator,
                     'flag_login': False, 'current_user': None, 'sort_by': self.sort_by,
                     'wh_q': self.request.GET.get(u'wh_q', 'checkin'), 'tab_num': tab_num
                     })


#
# View for FB canvas page
#
class PlaceViewCanvasPageHandler(PlaceListViewBaseHandler):
    def handle_fb_canvas_access_token(self):
        logger.debug("from fb_canvas")
        url_redirect_perm = "https://www.facebook.com/dialog/oauth?client_id=%s&redirect_uri=%s&scope=%s" % \
                (config.FACEBOOK_APP_ID, config.FACEBOOK_CANVAS_PAGE, config.FACEBOOK_PERMISSIONS_SCOPE)

        self.signed_req = self.request.POST.get('signed_request', None) or self.request.GET.get('signed_request', None)
        # logger.debug("self.signed_req: %s" % self.signed_req)
        if self.signed_req is None:
            return HttpResponse("<script> top.location.href='%s' </script>" % url_redirect_perm)
            #return HttpResponseRedirect(url_redirect_perm)

        self.signed_req_json = parse_signed_request(self.signed_req, config.FACEBOOK_APP_SECRET)
        logger.debug("self.signed_req_json: %s" % self.signed_req_json)

        if self.request.META.get('HTTP_ORIGIN', None) == r"http://apps.facebook.com":
            if self.signed_req_json.get(u'user_id') == None:
                # redirect to Permission request page
                return HttpResponse("<script> top.location.href='%s' </script>" % url_redirect_perm)
                #return HttpResponseRedirect(url_redirect_perm)

            if self.request.GET.get(u'code') != None and self.signed_req_json.get(u'oauth_token') == None:
                # redirect to login page
                url_redirect_code = "https://graph.facebook.com/oauth/authorize?client_id=%s&redirect_uri=%s" % \
                    (config.FACEBOOK_APP_ID, config.FACEBOOK_CANVAS_PAGE)
                return HttpResponse("<script> top.location.href='%s' </script>" % url_redirect_code)
                #return HttpResponseRedirect(url_redirect_code)
        
        self.access_token = self.signed_req_json.get(u'oauth_token', None)
        self.access_token_expires = self.signed_req_json.get(u'expires', None)
        self.uid = long(self.signed_req_json.get(u'user_id', -1))

        if self.access_token is None:
            return HttpResponse("<script> top.location.href='%s' </script>" % url_redirect_perm)
            #return HttpResponseRedirect(url_redirect_perm)
        return None
    

    def post(self, request, **kwargs):
        redirect = self.handle_fb_canvas_access_token()
        # redirect to permission or login page if access_token not found
        if redirect is not None:
            return redirect

        if is_mobile(request):
            template_dir = 'm'
        else:
            template_dir = 'w'

        # extend access token if expiring within a day
        self.access_token, self.access_token_expires = self.fb.get_extended_access_token_w_timeout(self.access_token, self.access_token_expires, DAY_IN_SECS)
        logger.debug("access_token: %s, expires:%s", self.access_token, self.access_token_expires)

        redirect = self.get_coordinate()
        #import pdb; pdb.set_trace()
        if redirect is not None:
            return redirect

        place_list = self.get_queryset()

        # message user to come back in a few minutes for the first time users
        if self.user is None or len(place_list) == 0:
            template_name = "%s/location_main_first_time_user.tmpl" % template_dir
            flag_first_time = True
            place_list = self.get_general_queryset()
        else:
            flag_first_time = False
            #import pdb; pdb.set_trace()
            template_name = '%s/location_main_canvas.tmpl' % template_dir
        location_paginator, page, page.object_list, is_paginated = self.paginate_queryset(place_list, kwargs['paginate_by'])
        # Make sure page request is an int. If not, deliver first page.
        try:
            page_num = int(request.GET.get('page', '1'))
        except ValueError:
            page_num = 1

        # If page request (9999) is out of range, deliver last page of results.
        try:
            page = location_paginator.page(page_num)
        except (EmptyPage, InvalidPage):
            page = location_paginator.page(location_paginator.num_pages)

        places = page.object_list
        recommend_list = []
        checkin_list = []
        if self.flag_recommend or flag_first_time:
            recommend_list = places
        else:
            checkin_list = places
        return render_to_response(template_name,
                   {'checkin_list': checkin_list, 'recommend_list': recommend_list, 
                    'app_url': config.FACEBOOK_CANVAS_PAGE, 'agent': request.META.get('HTTP_USER_AGENT', None),
                    'client_country': self.client_loc_country, 'client_state': self.client_loc_state, 
                    'client_city': self.client_loc_city, 'flag_geobrowsertried': request.GET.get('geobrowsertried', False),
                    'client_lat': self.client_loc_latitude, 'client_long': self.client_loc_longitude,
                    'ec2_page': config.EC2_APP_PAGE, 'access_token': self.access_token, 
                    'is_paginated': is_paginated, 'page': page, 'paginator': location_paginator,
                    'flag_login': False, 'current_user': None, 'sort_by': self.sort_by
                    })


#
# Base class for views that involves logins (invividual site)
#
class BaseLoginViewHandler(TemplateView):
    def __init__(self, **kwds):
        #import pdb;pdb.set_trace()
        super(TemplateView, self).__init__(**kwds)
        self.persistence = mpl.MongoPersistenceLayer()
        logger.debug("BaseLoginViewHandler.__init__() - kwds:%s" % kwds)

    def head(self, *args, **kwargs):
        logger.debug("BaseLoginViewHandler.head() - args:%s, kwargs:%s" % (args, kwargs))
        #import pdb;pdb.set_trace()
        return HttpResponse('')

    @property
    def current_user(self):
        """Returns the logged in Facebook user, or None if unconnected."""
        if not hasattr(self, "_current_user"):
            self._current_user = None
            user_id = whfb.parse_cookie(self.request.COOKIES.get("fb_user"))
            if user_id and str(user_id).isdigit():
                self._current_user = self.persistence.get_user(user_id)
        return self._current_user

    @current_user.setter
    def current_user(self, value):
        self._current_user = value


#
# Views for Individual Site
#
class PlaceViewIndividualSiteHandler(PlaceListViewBaseHandler, BaseLoginViewHandler):
    def __init__(self, **kwds):
        super(PlaceViewIndividualSiteHandler, self).__init__(**kwds)
        
    def post(self, request, **kwargs):
        #import pdb; pdb.set_trace()
        flag_login= True

        self.uid = whfb.parse_cookie(request.COOKIES.get("fb_user"))
        
        if self.uid is None:
            #return HttpResponseRedirect('/')
            current_user = None
            self.access_token = None
            self.access_token_expires = -1
        else:
            current_user = self.current_user
            self.access_token = current_user['access_token']
            self.access_token_expires = current_user['access_token_expires']

            # extend access token if expiring within a day
            self.access_token, self.access_token_expires = self.fb.get_extended_access_token_w_timeout(self.access_token, self.access_token_expires, DAY_IN_SECS)
            logger.debug("access_token: %s, expires:%s", self.access_token, self.access_token_expires)

        redirect = self.get_coordinate()
        if redirect is not None:
            user_id = whfb.parse_cookie(request.COOKIES.get("fb_user"))
            if user_id is not None:
                whfb.set_cookie(redirect, "fb_user", str(user_id), domain=config.WH_DOMAIN, path="/", expires=time.time() + 30 * 86400)
            return redirect

        place_list = self.get_queryset()

        app_url = config.WEBSITE_HOST + '/view.py'
        if is_mobile(request):
            template_dir = 'm'
        else:
            template_dir = 'w'

        if len(place_list) == 0:
            flag_first_time = True
            template_name = "%s/location_main_first_time_user.tmpl" % template_dir
            place_list = self.get_general_queryset()
        else:
            flag_first_time = False
            template_name = "%s/location_main.tmpl" % template_dir

        #import pdb; pdb.set_trace()
        location_paginator, page, page.object_list, is_paginated = self.paginate_queryset(place_list, kwargs['paginate_by'])
        # Make sure page request is an int. If not, deliver first page.
        try:
            page_num = int(request.GET.get('page', '1'))
        except ValueError:
            page_num = 1

        # If page request (9999) is out of range, deliver last page of results.
        try:
            page = location_paginator.page(page_num)
        except (EmptyPage, InvalidPage):
            page = location_paginator.page(location_paginator.num_pages)

        places = page.object_list
        recommend_list = []
        checkin_list = []
        if self.flag_recommend or flag_first_time:
            recommend_list = places
            wh_q = 'recommend'
        else:
            checkin_list = places
            wh_q = 'checkin'
        return render_to_response(template_name,
                                  {'checkin_list': checkin_list, 'recommend_list': recommend_list, 
                                   'app_url': app_url, 'agent': request.META.get('HTTP_USER_AGENT', None),
                                   'client_country': self.client_loc_country, 'client_state': self.client_loc_state, 
                                   'client_city': self.client_loc_city, 'flag_geobrowsertried': request.GET.get('geobrowsertried', False),
                                   'client_lat': self.client_loc_latitude, 'client_long': self.client_loc_longitude,
                                   'ec2_page': config.EC2_APP_PAGE, 'access_token': self.access_token, 
                                   'is_paginated': is_paginated, 'page': page, 'paginator': location_paginator,
                                   'flag_login': flag_login, 'current_user': current_user, 'sort_by': self.sort_by, 'wh_q': wh_q
                                   })


class HomeViewHandler(BaseLoginViewHandler):
    def get(self, request, **kwargs):
        logger.debug("HomeViewHandler.get()")
        #import pdb; pdb.set_trace()
        c_user = self.current_user
        if c_user is None or c_user.get('access_token', None) is None:
            args = dict(current_user=c_user)

            if is_mobile(request):
                template_dir = 'm'
            else:
                template_dir = 'w'
            response = render_to_response("%s/login_main.tmpl" % template_dir, args)
        else:
            args = dict(access_token=c_user['access_token'])
            response = HttpResponseRedirect("/view.py?" + urllib.urlencode(args))

        if self.request.COOKIES.get("fb_user", None) is not None:
            user_id = whfb.parse_cookie(self.request.COOKIES.get("fb_user"))
            whfb.set_cookie(response, "fb_user", str(user_id), domain=config.WH_DOMAIN, path="/", expires=time.time() + 30 * 86400)
        return response


class LoginViewHandler(BaseLoginViewHandler):
    def get(self, request, **kwargs):
        logger.debug("LoginHandler.get()")

        args = dict(client_id=config.FACEBOOK_APP_ID, 
                    redirect_uri="%s%s" % ( config.WEBSITE_HOST, request.META.get('PATH_INFO')),
                    state=config.FACEBOOK_APP_ID)

        if self.request.GET.get("code"):
            #import pdb; pdb.set_trace()
            args["client_secret"] = config.FACEBOOK_APP_SECRET
            args["code"] = self.request.GET.get("code")
            #response = cgi.parse_qs(urllib.urlopen(
            response = urlparse.parse_qs(urllib.urlopen(
                "https://graph.facebook.com/oauth/access_token?" +
                urllib.urlencode(args)).read())
            if response.get('access_token', None) is None:
                del args["client_secret"]
                del args["code"]
                return HttpResponseRedirect(
                    "https://www.facebook.com/dialog/oauth?" +
                    urllib.urlencode(args))

            access_token = response["access_token"][-1]
            access_token_expires = long(response["expires"][-1])

            # Download the user profile and cache a local instance of the
            # basic profile info
            profile = json.load(urllib.urlopen(
                "https://graph.facebook.com/me?" +
                urllib.urlencode(dict(access_token=access_token))))

            current_user = self.persistence.get_user(profile['id'])
            if current_user is None:  # no record in db
                current_user = {}
            
            current_user[u'_id'] = profile['id']
            current_user[u'name'] = profile['name']
            current_user[u'link'] = profile['link']
            current_user[u'access_token'] = access_token

            try:
                current_user[u'access_token_expires'] = long(access_token_expires)
            except:
                current_user[u'access_token_expires'] = 0

            self.persistence.save('user', current_user)

            self.client_loc_longitude = self.request.POST.get('longitude', None) or self.request.GET.get('longitude', None)
            self.client_loc_latitude = self.request.POST.get('latitude', None) or self.request.GET.get('latitude', None)
            
            if (self.client_loc_longitude is None or self.client_loc_latitude is None) and \
                    self.request.GET.get('geobrowsertried', None) is None:
                response = render_to_response('coordinate.tmpl', 
                                              {'app_url': config.WEBSITE_HOST + '/view.py', 'signed_request': None,
                                               'refresh_cnt': self.request.GET.get('c', 0), 'access_token': access_token})

            whfb.set_cookie(response, "fb_user", str(profile["id"]), path='/', domain=config.WH_DOMAIN, expires=time.time() + 30 * 86400)
            return response
        else:
            return HttpResponseRedirect(
#                "https://graph.facebook.com/oauth/authorize?" +
                "https://www.facebook.com/dialog/oauth?" +
                urllib.urlencode(args))


class LogoutViewHandler(BaseLoginViewHandler):
    def get(self, request, **kwargs):
        #import pdb; pdb.set_trace()
        logger.debug("LogoutHandler.get()")
        #response = HttpResponseRedirect("/")
        args = dict(current_user=None)

        if is_mobile(request):
            template_dir = 'm'
        else:
            template_dir = 'w'
        response = HttpResponseRedirect("/")
        #response = render_to_response("%s/login_main.tmpl" % template_dir, args)
        #whfb.set_cookie(response, "fb_user", "", expires=time.time() - 86400)
        whfb.set_cookie(response, "fb_user", "", domain=config.WH_DOMAIN, path="/", expires=time.time() - 86400)
        return response


#
# View that handle stale data request
#
class StaleDataViewHandler(View):
    def __init__(self, **kwds):
        super(View, self).__init__(**kwds)
        self.persistence = mpl.MongoPersistenceLayer()
        self.fb = whfb.Facebook(self.persistence)

    def get(self, request, **kwargs):
        logger.info("StaleDataViewHandler.get() - request:%s, kwargs:%s", request, kwargs)
        #import pdb; pdb.set_trace()
        access_token = request.GET.get('access_token', None)
        page_id = request.GET.get('page_id', None)
        new_page_id = self.fb.get_newid_attemp_w_graph_api(page_id, access_token)
        if page_id == new_page_id:
            response = HttpResponse(-1)
        else:
            self.persistence.remove_old_page_id(page_id)
            response = HttpResponse(new_page_id)
        return response


#
# View that handle opeining FB place page
#
'''
class OpenFBPlacePageViewHandler(View):
    def __init__(self, **kwds):
        super(View, self).__init__(**kwds)
        self.persistence = mpl.MongoPersistenceLayer()
        self.fb = whfb.Facebook(self.persistence)

    def get(self, request, **kwargs):
        logger.info("OpenFBPlacePageViewHandler.get() - request:%s, kwargs:%s", request, kwargs)
        #import pdb; pdb.set_trace()
        access_token = request.GET.get('access_token', None)
        page_id = request.GET.get('page_id', None)
        new_page_id = self.fb.get_newid_attemp_w_graph_api(page_id, access_token)
        if page_id == new_page_id:
            response = HttpResponse(-1)
        else:
            self.persistence.remove_old_page_id(page_id)
            response = HttpResponse(new_page_id)
        return response
'''

def parse_signed_request(signed_request, secret):
    l = signed_request.split('.', 2)
    encoded_sig = l[0]
    payload = l[1]

    sig = base64_url_decode(encoded_sig)
    data = json.loads(base64_url_decode(payload))
    return data


def base64_url_decode(inp):
    padding_factor = (4 - len(inp) % 4) % 4
    inp += "="*padding_factor 
    return base64.b64decode(unicode(inp).translate(dict(zip(map(ord, u'-_'), u'+/'))))


def close(request):
    return HttpResponse("<html><head><script language='javascript'>window.close()</script></head></html>")


def is_mobile(request):
    logger.info("is_mobile - agent: %s" % request.META.get('HTTP_USER_AGENT', ''))
    agent = request.META.get('HTTP_USER_AGENT', '')
    if string.find(agent, 'Android') != -1 or string.find(agent, 'webOS') != -1 or \
            string.find(agent, 'iPhone') != -1 or string.find(agent, 'iPod') != -1:
        return True
    return False


