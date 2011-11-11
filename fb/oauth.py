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

from appengine_config import *
from django.utils import simplejson as json
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api import taskqueue
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

    @property
    def linktext(self):
        self._linktext = 'My Hangouts' if self.request.cookies.get("fb_user") else 'Sign-in'
        return self._linktext

        
class LogoutHandler(BaseHandler):
    def get(self):
        user = self.current_user
        try:
            logging.info('INFO: %s - %s Logging Out' % (user.id, user.name))
            set_cookie(self.response, "fb_user", "", expires=time.time() - 86400)
        except:
            logging.error('ERROR: Logging error w/ logging out')
        self.redirect("/")


class LoginHandler(BaseHandler):
    def get(self):
        verification_code = self.request.get("code")
        args = dict(client_id=FACEBOOK_APP_ID,
                    redirect_uri=self.request.path_url,
                    scope='email,user_likes')
        if self.request.get("code"):
            args["client_secret"] = FACEBOOK_APP_SECRET
            args["code"] = self.request.get("code")
            response = cgi.parse_qs(urllib2.urlopen(
                "https://graph.facebook.com/oauth/access_token?" +
                urllib.urlencode(args)).read())
            access_token = response["access_token"][-1]

            # Try too look up user in our DB by access_token
            user = db.GqlQuery("SELECT * FROM fbUser WHERE access_token = '%s'" %
                               access_token).get()
            if user:
                id = user.id
                logging.info('INFO: %s - %s  User Found' % (id, user.name))
                if user.likes is None:
                    taskqueue.add(url="/refresh", params={'key': str(user.key())})
            else:
                # Create a user, download the user profile and store basic profile info
                profile = json.load(urllib2.urlopen(
                        "https://graph.facebook.com/me?" +
                        urllib.urlencode(dict(access_token=access_token))))
                user = fbUser(key_name=str(profile["id"]),
                              id=str(profile["id"]),
                              email=str(profile['email']),
                              name=profile["name"],
                              access_token=access_token,
                              profile_url=profile["link"])
                user.put()
                id = profile["id"]
                logging.info('INFO: %s - %s Adding New User' % (id, user.name))
                taskqueue.add(url="/refresh", params={'key': str(user.key())})
                
            set_cookie(self.response, "fb_user", str(id),
                       expires=time.time() + 30 * 86400)
            self.redirect('/user')
            
        else:
            self.redirect(
                "https://graph.facebook.com/oauth/authorize?" +
                urllib.urlencode(args))
        
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
