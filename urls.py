from google.appengine.dist import use_library
use_library('django', '1.2')

import os
from fb.oauth import *
from main import *
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

application = webapp.WSGIApplication([('/', MainPage),
                                      ('/auth/login', LoginHandler),
                                      ('/auth/logout', LogoutHandler),
                                      ('/user', UserPage),
                                      ('/edit', EditPage),
                                      ('/about', AboutPage),
                                      ('/refresh', RefreshTask),
                                      ('/faq', FAQPage),
                                      ('/event', EventPage),
                                      ('/profilepic', ProfilePic),
                                      ('/unjoin', Unjoin),
                                      ('/score', Score),
                                      ('/unjointask', UnjoinTask),
                                      ('/hunch', Hunch),
                                      ('/deletetask', DeleteTask),
                                      ('/purge', EventPurge),
                                      ('/expire', ExpireDaemon),
                                      ('/expiretask', ExpireTask),
                                      ('/home', MainPage),
                                      ('/join', Join),
                                      ('/browse', Browse),
                                      ('/future', Future),
                                      ('/create', CreatePage),
                                      ('/post', EventPage),
                                      ('/geo', Geo)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
