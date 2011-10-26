"""
Future Facebook Dataflow
------------------------------
after /fb/auth/login, redirects to oauth.html  - this should instead...

1. store user's likes 
2. store user's profile picture 'http://graph.facebook.com/%s/picture' % self.current_user.id
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
        
from google.appengine.dist import use_library
use_library('django', '1.2')
from django.utils import simplejson as json
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
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


class HomeHandler(BaseHandler):
    def get(self):
        ### MAKE THIS LOAD PROFILE ONLY IF IT HASNT LOADED IN THE LAST 24hrs
        user=self.current_user
        graph = facebook.GraphAPI(user.access_token)
        likes = graph.get_object("/me/likes")
        likes = likes['data']
        user.likes = [like['id'] for like in likes]

        picture = urllib2.urlopen('http://graph.facebook.com/%s/picture' % self.current_user.id).read()
        user.picture = db.Blob(picture)
        user.put()

        # display picture w/ appropriate headers
        self.response.headers['Content-Type'] = 'image/jpeg'
        self.response.out.write(picture)
        
        #path = os.path.join(os.path.dirname(__file__), "../static/oauth.html")
        #args = dict(current_user=self.current_user)
        #self.response.out.write(template.render(path, args))
        #self.response.out.write('<img src="http://graph.facebook.com/%s/picture"/>' % self.current_user.id)

        
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
            profile = json.load(urllib2.urlopen(
                "https://graph.facebook.com/me?" +
                urllib.urlencode(dict(access_token=access_token))))
            user = fbUser(key_name=str(profile["id"]), id=str(profile["id"]),
                        name=profile["name"], access_token=access_token,
                        profile_url=profile["link"])
            user.put()

            set_cookie(self.response, "fb_user", str(profile["id"]),
                       expires=time.time() + 30 * 86400)
            self.redirect("/fb/")
        else:
            self.redirect(
                "https://graph.facebook.com/oauth/authorize?" +
                urllib.urlencode(args))


class LogoutHandler(BaseHandler):
    def get(self):
        set_cookie(self.response, "fb_user", "", expires=time.time() - 86400)
        self.redirect("/fb/")


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


def main():
    util.run_wsgi_app(webapp.WSGIApplication([(r"/fb/", HomeHandler),
                                              (r"/fb/auth/login", LoginHandler),
                                              (r"/fb/auth/logout", LogoutHandler)],
                                             debug=True))


if __name__ == "__main__":
    main()