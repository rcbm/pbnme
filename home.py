import os
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

class MainPage(webapp.RequestHandler):
    def get(self):
        self.response.out.write('PENUSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS')

class Secret(webapp.RequestHandler):
    def get(self):
        self.response.out.write('SECREEEEEEEETTTTTTTTTTTTT')
