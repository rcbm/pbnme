from google.appengine.dist import use_library
use_library('django', '1.2')

import os
from main import *
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

application = webapp.WSGIApplication([('/', MainPage),
                                      ('/test', Test),
                                      ('/event', EventPage),
                                      ('/unjointask', UnjoinTask),
                                      ('/deletetask', DeleteTask),
                                      ('/purge', EventPurge),
                                      ('/home', MainPage),
                                      ('/user', UserPage),
                                      ('/join', Join),
                                      ('/browse', Browse),
                                      ('/create', Create),
                                      ('/post', EventPage)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
