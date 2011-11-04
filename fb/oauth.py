"""
Future Facebook Dataflow
------------------------------
after /fb/auth/login, redirects to oauth.html  - this should instead...

1. store user's likes 
2. store user's profile picture 'http://graph.facebook.com/%s/picture' % self.current_user.id


########
Refactor models.py away from UserProperty()
"""

FACEBOOK_APP_ID = "231959676859483"
FACEBOOK_APP_SECRET = "7c3857ee6170df4246cfffbf1544591e"

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
import urllib2
import wsgiref.handlers
import fb.facebook as facebook
        
from django.utils import simplejson as json
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
from datetime import datetime
from models import *

class BaseHandler(webapp.RequestHandler):
    @property
    def current_user(self):
        """Returns the logged in Facebook user, or None if unconnected."""
        if not hasattr(self, "_current_user"):
            self._current_user = None
            user_id = parse_cookie(self.request.cookies.get("fb_user"))
            if user_id:
                self._current_user = fbUser.get_by_key_name(user_id)
        return self._current_user

class FBUpdateHandler(webapp.RequestHandler):
    def __init__(self, user):
        self.user = user;

    def load(self):
        # Loads FB Profile Info
        # Should only be run if now() - last >72hrs
        user = self.user
        graph = facebook.GraphAPI(user.access_token)

        # Download Likes
        likes = graph.get_object("/me/likes")
        likes = likes['data']
        user.likes = [like['id'] for like in likes]

        # Download Picture
        picture = urllib2.urlopen('http://graph.facebook.com/%s/picture' % user.id).read()
        user.picture = db.Blob(picture)
        user.updated = datetime.now()
        user.put()
        
class LoginHandler(BaseHandler):
    def get(self):
        verification_code = self.request.get("code")
        args = dict(client_id=FACEBOOK_APP_ID, redirect_uri=self.request.path_url)
        if self.request.get("code"):
            args["client_secret"] = FACEBOOK_APP_SECRET
            args["code"] = self.request.get("code")
            response = cgi.parse_qs(urllib2.urlopen(
                "https://graph.facebook.com/oauth/access_token?" +
                urllib.urlencode(args)).read())
            access_token = response["access_token"][-1]

            # Download the user profile and cache a local instance of the
            # basic profile info
            ### THIS IS NUKING DATA AT EVERY LOGIN
            if self.current_user:
                logging.info('########### FOUND USDRRDFSDFSDF ##########')

            logging.info('TOKEN: %s' % access_token)
            user = db.GqlQuery("SELECT * FROM fbUser WHERE access_token = '%s'" %
                                        access_token).get()
            if user:
                logging.info('################ LOOKED UP USER #############')
                set_cookie(self.response, "fb_user", str(user.id),
                           expires=time.time() + 30 * 86400)
            else:
                logging.info('################ COULDN"T LOOK UP ###########')

                profile = json.load(urllib2.urlopen(
                    "https://graph.facebook.com/me?" +
                    urllib.urlencode(dict(access_token=access_token))))
                user = fbUser(key_name=str(profile["id"]), id=str(profile["id"]),
                            name=profile["name"], access_token=access_token,
                            profile_url=profile["link"])
                user.put()

                set_cookie(self.response, "fb_user", str(profile["id"]),
                           expires=time.time() + 30 * 86400)
            self.redirect('/user')
        else:
            self.redirect(
                "https://graph.facebook.com/oauth/authorize?" +
                urllib.urlencode(args))
        
class LogoutHandler(BaseHandler):
    def get(self):
        logging.debug('####### logging out #########')
        set_cookie(self.response, "fb_user", "", expires=time.time() - 86400)
        self.redirect("/")


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
    response.headers._headers.append(("Set-Cookie", cookie.output()[12:]))


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
    hash = hmac.new(FACEBOOK_APP_SECRET, digestmod=hashlib.sha1)
    for part in parts: hash.update(part)
    return hash.hexdigest()
