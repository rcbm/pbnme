'''
THINGS TO-DO:
-------------
* Break DeleteHandler into tasks
* Join button should be hidden when viewing a group you already belong to
  (check both event's members and user's events? -- these should not be out of sync)

Fix alignment issue w/ logo
Fix security hole for directly accessing *.html files
Add existing group checking for create()
Add date conflict checking for create()
Implement 'default-value' checking to create form in JS
Make a safe-guard that if manually deleting an event (on the backend),
  the reference in the user-profiles is also deleted... maybe when a user loads their page?
Show a 'delete' group button on /user if zero-members in group

DONE
-------------
* Template out /browse
* Template out /user
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

class DeleteHandler(webapp.RequestHandler):
    def get(self):
        ekey = self.request.get('key')
        event = db.get(ekey)
        # step 1. Iter through each member in the group, delete this group from their 'groups'
        for event_member in event.members:
            member = db.get(event_member)
            member.events = [s for s in member.events if str(s) != ekey]
            member.put()
        # step 2. delete the group itself
        db.delete(event)
        
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
                           'members': [db.get(m) for m in event.members],
                           'join_button': False if current_user in event.members else True}
        self.response.out.write(template.render('static/event.html', template_values))

class UserPage(webapp.RequestHandler):
    def get(self):
        linktext = 'My Events' if users.get_current_user() else 'Login'
        if users.get_current_user():
            existing_user = db.GqlQuery("SELECT * FROM User WHERE user_id = '%s'" % users.get_current_user().user_id()).get()
            events = [db.get(event) for event in existing_user.events] if existing_user else []
            template_values = {'logout': users.create_logout_url("/"),
                               'linktext': linktext,
                               'events': events}
            self.response.out.write(template.render('static/user.html', template_values))
        else:
            self.redirect(users.create_login_url(self.request.uri))

class MainPage(webapp.RequestHandler):
    def get(self):
        linktext = 'My Events' if users.get_current_user() else 'Login'
        template_values = {'linktext': linktext}
        self.response.out.write(template.render('static/index.html', template_values))

class Browse(webapp.RequestHandler):
    def get(self):
        linktext = 'My Events' if users.get_current_user() else 'Login'
        events = db.GqlQuery("SELECT * FROM Event LIMIT 100")
        template_values = {'linktext': linktext,
                           'events': events}
        self.response.out.write(template.render('static/browse.html', template_values))
        
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
            if existing_user:
                event = Event(creator = current_user,
                              create_date = now,
                              title = title,
                              description = description,
                              members = [existing_user.key()])
                event.put()
                existing_user.events.append(event.key())
                existing_user.put()
                self.redirect("/event?key=%s" % event.key())
            else:
                user_profile = User(user = current_user,
                                    user_id = current_user.user_id(),
                                    email = current_user.email(),
                                    create_date = now,
                                    last_date = now)
                user_profile.put()
                event = Event(creator = current_user,
                              create_date = now,
                              title = title,
                              description = description,
                              members = [user_profile.key()])
                event.put()
                # In order to have both the event and the user reference each other
                # one has to be saved and then retrieved and saved again (so as to generate a key)
                user_profile.events = [event.key()]
                user_profile.put()
                self.redirect("/event?key=%s" % event.key())
        else:
            self.redirect(users.create_login_url(self.request.uri))
