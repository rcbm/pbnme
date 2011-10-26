'''
THINGS TO-DO:
-------------
* implement /join as an ajax call (using post())

* add un-join button to /user
* sort events by # of people attending

Not Urgent
_____________
Fix datetime
  - change str(today) to datetime.date.today()
  - add datepicker
  - implement date and time ranges(i think they just subtract?)

When there are no hangouts in /browse, add a 'create' message
Fix alignment issue w/ logo
Add existing group checking for create()
Add date conflict checking for create()
Implement 'default-value' checking to create form in JS
Make a safe-guard that if manually deleting an event (on the backend),
  the reference in the user-profiles is also deleted... maybe when a user loads their page?

Harder:
-------------
[implement form validation w/ js and python]
[Add uploading of a photo when creating a hangout]
[Add Geolocation (http://diveintohtml5.org/geolocation.html)]
[Add Facebook (http://developers.facebook.com/docs/reference/api/)]


###########################################################################################

DONE
-------------
* implement /delete as an ajax call (using post())
* add # of people attending on main events list page
* add hiding for non-owners, show a 'delete' group button on /user if zero-members in group
* Add date/time
* Template out /browse
* Add location to pages and db
* Template out /user
* Check to see if I don't already belong to an event, if so don't show 'join' button
* Join button should be hidden when viewing a group you already belong to
  (check both event's members and user's events? -- these should not be out of sync)
* add a way of showing some (or all) events on index.html

Break DeleteHandler into tasks
Add a number system for people who are going to an event
Fix security hole for directly accessing *.html files
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
from google.appengine.api import taskqueue
from models import *
        
class EventPurge(webapp.RequestHandler):
    # Takes an event by key and removes itself from all its members
    def post(self):
        eventKey = self.request.get('key')
        event = db.get(eventKey)

        for event_member in event.members:
            taskqueue.add(url="/unjointask", params={'userKey': event_member,
                                                     'eventKey': eventKey})
            # step 2. delete the group itself
            taskqueue.add(url="/deletetask", params={'key': eventKey})
        
class DeleteTask(webapp.RequestHandler):
    # Takes a key and deletes its corresponding entity
    def post(self):
        db.delete(self.request.get('key'))
        
class UnjoinTask(webapp.RequestHandler):
    # Takes an event and user
    # removes the user from the given event
    def post(self):
        member = db.get(self.request.get('userKey'))
        member.events = [s for s in member.events if str(s) != self.request.get('eventKey')]
        member.put()

class Join(webapp.RequestHandler):
    def get(self):
        current_user = users.get_current_user()
        if current_user:
            key = self.request.get('key')
            event = db.get(key)
            user = db.GqlQuery("SELECT * FROM User WHERE user_id = '%s'" % users.get_current_user().user_id()).get()
            # Make sure user isn't already part of the event
            if user:
                if user.key() not in event.members:
                    user.events.append(db.Key(key))
                    user.put()
                    event.members.append(user.key())
                    event.put()
                    self.redirect('/user')
            else:
                now = datetime.datetime.now()
                user_profile = User(user = current_user,
                                    user_id = current_user.user_id(),
                                    email = current_user.email(),
                                    create_date = now,
                                    last_date = now,
                                    events = [event.key()])
                user_profile.put()
                event.members.append(user_profile.key())
                event.put()
                self.redirect('/user')
        else:
            self.redirect(users.create_login_url(self.request.uri))

class EventPage(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            existing_user = db.GqlQuery("SELECT * FROM User WHERE user_id = '%s'" % user.user_id()).get()
        else:
            existing_user = None
        
	    posts = db.GqlQuery("SELECT * "
	                            "FROM Post "
	                            "WHERE ANCESTOR IS :1 "
	                            "ORDER BY date DESC LIMIT 10",
	                             guestbook_key(guestbook_name))
	
	
	
	"""	
		for post in posts:
		            if post.author:
		                self.response.out.write('<b>%s</b> wrote:' % post.author.nickname())
		            else:
		                self.response.out.write('An anonymous person wrote:')
		            self.response.out.write('<blockquote>%s</blockquote>' %
		                                    cgi.escape(greeting.content))
	"""	
        key = self.request.get('key')
        event = db.get(key)
        linktext = 'My Hangouts' if user else 'Login'
        template_values = {'linktext': linktext,
                           'key': event.key(),
                           'title': event.title,
                           'location': event.location,
                           'datetime': event.datetime,
                           'description': event.description,
                           'members': [db.get(m) for m in event.members],
                           'join_button': False if existing_user and existing_user.key() in event.members else True}
        self.response.out.write(template.render('static/event.html', template_values))

"""
This is just here as a reference for me

		def post(self):
	        current_user = users.get_current_user()
	        if current_user:
	            from dateutil import parser
	            title = self.request.get('title')
	            location = self.request.get('location')
	            description = self.request.get('description')
	            existing_user = db.GqlQuery("SELECT * FROM User WHERE user_id = '%s'" % current_user.user_id()).get()
	            now = datetime.datetime.now()
	            time = self.request.get('time')
	            date = self.request.get('date')
	            if existing_user:
	                event = Event(creator = current_user,
	                              create_date = now,
	                              title = title,
	                              location = location,
	                              datetime = parser.parse('%s %s' %(date, time), fuzzy=True),
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
	                # Maybe change create_date = now w/ Auto_Now_Add=True in models.py
	                event = Event(creator = current_user,
	                              create_date = now,
	                              title = title,
	                              location = location,
	                              datetime = parser.parse('%s %s' %(date, time), fuzzy=True),
	                              description = description,
	                              members = [user_profile.key()])
	                event.put()
	                # In order to have both the event and the user reference each other
	                # one has to be saved and then retrieved and saved again (so as to generate a db.Key)
	                user_profile.events = [event.key()]
	                user_profile.put()
	                self.redirect("/event?key=%s" % event.key())
	        else:
	            self.redirect(users.create_login_url(self.request.uri))

#this is the post in progress

	def post(self):
		current_user = users.get_current_user()
        
        if current_user:
	        from dateutil import parser
            existing_user = db.GqlQuery("SELECT * FROM User WHERE user_id = '%s'" % current_user.user_id()).get()
            now = datetime.datetime.now()
            time = self.request.get('time')
            date = self.request.get('date')
			key = self.request.get('key') 
		    event = db.get(key)
            comment_content = self.request.get('comment_content') 

			comment = Post(author = current_user,
                      	   create_date = now,
                           comment = comment_content,
                           location = location,
                           event = key)
            post.put()
			event.posts.append(comment.key())
            event.put()
            self.redirect("/event?key=%s" % event.key())
"""
	
class UserPage(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        linktext = 'My Hangouts' if users.get_current_user() else 'Login'
        if user:
            existing_user = db.GqlQuery("SELECT * FROM User WHERE user_id = '%s'" % user.user_id()).get()
            events = [db.get(event) for event in existing_user.events] if existing_user else []
            template_values = {'current_user': user,
                               'logout': users.create_logout_url("/"),
                               'linktext': linktext,
                               'events': events}
            self.response.out.write(template.render('static/user.html', template_values))
        else:
            self.redirect(users.create_login_url(self.request.uri))

class MainPage(webapp.RequestHandler):
    def get(self):
        linktext = 'My Hangouts' if users.get_current_user() else 'Login'
        events = db.GqlQuery("SELECT * FROM Event LIMIT 100")
        template_values = {'linktext': linktext,
                           'events': events}
        self.response.out.write(template.render('static/index.html', template_values))

class Browse(webapp.RequestHandler):
    def get(self):
        linktext = 'My Hangouts' if users.get_current_user() else 'Login'
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
        linktext = 'My Hangouts' if users.get_current_user() else 'Login'
        template_values = {'linktext': linktext}
        self.response.out.write(template.render('static/create.html', template_values))
        
    def post(self):
        current_user = users.get_current_user()
        if current_user:
            from dateutil import parser
            title = self.request.get('title')
            location = self.request.get('location')
            description = self.request.get('description')
            existing_user = db.GqlQuery("SELECT * FROM User WHERE user_id = '%s'" % current_user.user_id()).get()
            now = datetime.datetime.now()
            time = self.request.get('time')
            date = self.request.get('date')
            if existing_user:
                event = Event(creator = current_user,
                              create_date = now,
                              title = title,
                              location = location,
                              datetime = parser.parse('%s %s' %(date, time), fuzzy=True),
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
                # Maybe change create_date = now w/ Auto_Now_Add=True in models.py
                event = Event(creator = current_user,
                              create_date = now,
                              title = title,
                              location = location,
                              datetime = parser.parse('%s %s' %(date, time), fuzzy=True),
                              description = description,
                              members = [user_profile.key()])
                event.put()
                # In order to have both the event and the user reference each other
                # one has to be saved and then retrieved and saved again (so as to generate a db.Key)
                user_profile.events = [event.key()]
                user_profile.put()
                self.redirect("/event?key=%s" % event.key())
        else:
            self.redirect(users.create_login_url(self.request.uri))
