#!/usr/bin/env python
#
# Copyright 2010 Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""A barebones AppEngine application that uses Facebook for login.

This application uses OAuth 2.0 directly rather than relying on Facebook's
JavaScript SDK for login. It also accesses the Facebook Graph API directly
rather than using the Python SDK. It is designed to illustrate how easy
it is to use the Facebook Platform without any third party code.

See the "appengine" directory for an example using the JavaScript SDK.
Using JavaScript is recommended if it is feasible for your application,
as it handles some complex authentication states that can only be detected
in client-side code.
"""

import base64
import cgi
import Cookie
import email.utils
import hashlib
import hmac
import logging
import os.path
import time
import urllib
import wsgiref.handlers

from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import classonlymethod

from django.utils import simplejson as json
from django.views.generic import TemplateView

import config
import mongo_persistence_layer as mpl

logger = logging.getLogger(__name__)


class BaseHandler(TemplateView):
    
    def __init__(self, **kwds):
        super(TemplateView, self).__init__(**kwds)
        self.persistence = mpl.MongoPersistenceLayer()

    @property
    def current_user(self):
        """Returns the logged in Facebook user, or None if unconnected."""
        if not hasattr(self, "_current_user"):
            self._current_user = None
            user_id = parse_cookie(self.request.COOKIES.get("fb_user"))
            if user_id:
                self._current_user = self.persistence.get_user(user_id)
        return self._current_user

    @current_user.setter
    def current_user(self, value):
        self._current_user = value


class HomeHandler(BaseHandler):
    def get(self, request, **kwargs):
        logger.debug("HomeHandler.get()")
        args = dict(current_user=self.current_user)
        return render_to_response("oauth.html", args)


class LoginHandler(BaseHandler):
    def get(self, request, **kwargs):
        logger.debug("LoginHandler.get()")
        verification_code = self.request.GET.get("code")
        self.request.path_url = "http://%s%s" % ( config.WEBSITE_HOST, request.META.get('PATH_INFO'))
        logger.debug("path_url:%s" % self.request.path_url)
        args = dict(client_id=config.FACEBOOK_APP_ID, redirect_uri=self.request.path_url)

        if self.request.GET.get("code"):
            args["client_secret"] = config.FACEBOOK_APP_SECRET
            args["code"] = self.request.GET.get("code")
            response = cgi.parse_qs(urllib.urlopen(
                "https://graph.facebook.com/oauth/access_token?" +
                urllib.urlencode(args)).read())
            access_token = response["access_token"][-1]

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
            current_user[u'access_token'] =access_token

            self.current_user = current_user
            logger.debug("current_user:%s" % self.current_user)
            self.persistence.save('user', self.current_user)

            self.response = HttpResponseRedirect("/")
            set_cookie(self.response, "fb_user", str(profile["id"]),
                       expires=time.time() + 30 * 86400)
            return self.response
        else:
            return HttpResponseRedirect(
                "https://graph.facebook.com/oauth/authorize?" +
                urllib.urlencode(args))


class LogoutHandler(BaseHandler):
    def get(self, request, **kwargs):
        logger.debug("LogoutHandler.get()")
        self.response = HttpResponseRedirect("/")
        set_cookie(self.response, "fb_user", "", expires=time.time() - 86400)
        return self.response


def set_cookie(response, name, value, domain=None, path="/", expires=None):
    """Generates and signs a cookie for the give name/value"""
    timestamp = str(int(time.time()))
    value = base64.b64encode(value)
    signature = cookie_signature(value, timestamp)
    cookie = Cookie.BaseCookie()
    cookie[name] = "|".join([value, timestamp, signature])
    cookie[name]["path"] = path
    if domain: cookie[name]["domain"] = domain
    if expires:
        cookie[name]["expires"] = email.utils.formatdate(
            expires, localtime=False, usegmt=True)
    response["Set-Cookie"] = cookie.output()[12:]


def parse_cookie(value):
    """Parses and verifies a cookie value from set_cookie"""
    if not value: return None
    parts = value.split("|")
    if len(parts) != 3: return None
    if cookie_signature(parts[0], parts[1]) != parts[2]:
        logging.warning("Invalid cookie signature %r", value)
        return None
    timestamp = int(parts[1])
    if timestamp < time.time() - 30 * 86400:
        logging.warning("Expired cookie %r", value)
        return None
    try:
        return base64.b64decode(parts[0]).strip()
    except:
        return None


def cookie_signature(*parts):
    """Generates a cookie signature.

    We use the Facebook app secret since it is different for every app (so
    people using this example don't accidentally all use the same secret).
    """
    hash = hmac.new(config.FACEBOOK_APP_SECRET, digestmod=hashlib.sha1)
    for part in parts: hash.update(part)
    return hash.hexdigest()

