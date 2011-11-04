from google.appengine.dist import use_library
use_library('django', '1.2')

import os
from fb.oauth import *
from main import *
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

application = webapp.WSGIApplication([('/', MainPage),
                                      ('/fb', UserPage),
                                      ('/fb/auth/login', LoginHandler),
                                      ('/fb/auth/logout', LogoutHandler),
                                      ('/user', LoginHandler),
                                      ('/about', AboutPage),
                                      ('/faq', FAQPage),
                                      ('/event', EventPage),
                                      ('/unjointask', UnjoinTask),
                                      ('/deletetask', DeleteTask),
                                      ('/purge', EventPurge),
                                      ('/home', MainPage),
                                      ('/join', Join),
                                      ('/browse', Browse),
                                      ('/create', CreatePage),
                                      ('/post', EventPage)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
