import os
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api import users

class UserPage(webapp.RequestHandler):
    def get(self):
        if users.get_current_user():
            url = users.create_logout_url("/")
            url_linktext = 'Logout'
            self.response.out.write("You're Logged In!<br><br>")
            self.response.out.write('<a href="/">Home</a><br>')
            self.response.out.write('<a href="%s">%s</a>' %(url, url_linktext))
        else:
            self.redirect(users.create_login_url(self.request.uri))

class MainPage(webapp.RequestHandler):
    def get(self):
        url = "/user"
        if users.get_current_user():
            url_linktext = 'My Events'
        else:
            url_linktext = 'Login'

        template_values = {
            'url': url,
            'url_linktext': url_linktext,
            }
            
        path = 'index.html'
        self.response.out.write(template.render(path, template_values))

class Secret(webapp.RequestHandler):
    def get(self):
        self.response.out.write('SECREEEEEEEETTTTTTTTTTTTT')

