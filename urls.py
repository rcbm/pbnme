import os
from main import *
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

application = webapp.WSGIApplication([('/', MainPage),
                                      ('/user', UserPage),
                                      ('/secret', Secret)],
                                     debug=True)
def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
