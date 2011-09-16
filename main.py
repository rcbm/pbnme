'''
THINGS TO-DO:
-------------
Fix alignment issue w/ logo
Fix security hole for directly accessing *.html files
Add existing group checking for create()
Add date conflict checking for create()
Implement 'default-value' checking to create form in JS
Make a safe-guard that if manually deleting an event, the reference in the user-profiles is also deleted
Show a 'delete' group button on /user if zero-members in group

DONE
-------------
* Check to see if I don't already belong to an event, if so don't show 'join' button
Change default-value in forms to change depending on FOCUS not on click
Auto-Join people who create an event
Change create() to redirect to event template
Create event template

'''

import os
import datetime
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api import users
from models import *

class Join(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            key = self.request.get('key')
            user = db.GqlQuery("SELECT * FROM User WHERE user_id = '%s'" % users.get_current_user().user_id()).get()
            user.events.append(db.Key(key))
            user.put()
            self.redirect('/user')
        else:
            self.redirect(users.create_login_url(self.request.uri))

class EventPage(webapp.RequestHandler):
    def get(self):
        current_user = users.get_current_user()
        key = self.request.get('key')
        event = db.get(key)
        linktext = 'My Events' if current_user else 'Login'
        template_values = {'linktext': linktext,
                           'key': event.key(),
                           'title': event.title,
                           'description': event.description,
                           'members': event.members,
                           'join_button': False if current_user in event.members else True}
        self.response.out.write(template.render('static/event.html', template_values))

class UserPage(webapp.RequestHandler):
    def get(self):
        if users.get_current_user():
            self.response.out.write("You're Logged In!<br>")
            self.response.out.write('<a href="/">Home</a> | <a href="%s">Logout</a> | <a href="/browse">Join</a> | <a href="/create">Create</a>' % users.create_logout_url("/"))
            self.response.out.write('<h1>List of all events:</h1><br>')
            existing_user = db.GqlQuery("SELECT * FROM User WHERE user_id = '%s'" % users.get_current_user().user_id()).get()
            events = existing_user.events if existing_user else []
            for event in events:
                self.response.out.write('<a href="/event?key=%s">%s</a><br>' % (event, db.get(event).title))
        else:
            self.redirect(users.create_login_url(self.request.uri))

class MainPage(webapp.RequestHandler):
    def get(self):
        linktext = 'My Events' if users.get_current_user() else 'Login'
        template_values = {'linktext': linktext}
        self.response.out.write(template.render('static/index.html', template_values))

class Browse(webapp.RequestHandler):
    def get(self):
        self.response.out.write('<h1>List of all events:</h1><br>')
        events = db.GqlQuery("SELECT * FROM Event LIMIT 100")
        for event in events:
            self.response.out.write('<a href="/event?key=%s">%s</a><br>' % (event.key(), event.title))

class Create(webapp.RequestHandler):
    ####
    # if user exists, make an event and add it to their eventslist
    # else create the user first
    ####
    def get(self):
        linktext = 'My Events' if users.get_current_user() else 'Login'
        template_values = {'linktext': linktext}
        self.response.out.write(template.render('static/create.html', template_values))
        
    def post(self):
        current_user = users.get_current_user()
        if current_user:
            title = self.request.get('title')
            description = self.request.get('description')
            existing_user = db.GqlQuery("SELECT * FROM User WHERE user_id = '%s'" % current_user.user_id()).get()
            now = datetime.datetime.now()
            event = Event(creator = current_user, create_date = now, title = title, description = description, members = [current_user])
            event.put()
            if existing_user:
                existing_user.events.append(event.key())
                existing_user.put()
                self.redirect("/event?key=%s" % event.key())
            else:
                user_profile = User(user = current_user, user_id = current_user.user_id(), email = current_user.email(), create_date = now, last_date = now)
                user_profile.events = [event.key()]
                user_profile.put()
                self.redirect("/event?key=%s" % event.key())
        else:
            self.redirect(users.create_login_url(self.request.uri))
