'''
Future Sketches
-------------------------
VERSION a2:

Differences
- list of links on front page, logo remains same, tagline remains but is near top
- tagline ends w/ facebook login prompt
- footer needs to be rethought, esp. for front page


GEOLOCATION:
Users in Berkeley CA and Pittsburgh PA can log in and create events.
Users in other places can only see events but cannot create or join them.
If they try they'll get a polite message and a promise we'll contact them
when its available in their city.



FACEBOOK:
When a user logs in we sign them in w/ FB. Then we see if we have the
user's information in our datastore. If we do, has it been updated recently? (~72hrs)

FB Information we keep on hand: 
 - ID
 - Name
 - Small Photo
 - Access Token
 - List of Likes
 - (List of Friends?)

QUESTIONS:
How do we deal w/ people who don't have facebook? Landing page?
Where does this page go? How much stuff do we actually store?
Do we need a list of friends... for the matching algorithm?




EXPIRING EVENTS:
An event has a Datetime when it is to occur, and a
active flag. When machinetime > an events Datetime,
this Event should flip the active flag. This means that machinetime
must be monitoring machinetime. Is there a continuous process for
this? Or can we have a task execute this whenever a user performs
some action?



 

THINGS TO-DO:

URGENT
-------------
* swap Google Users to FB
* add content to FAQ (hook already made)
* add content to About (hook already made)
* implement email and/or fb message reminders
* make more robust /browse (sort by date, sort by score, etc.)
* implement /join as an ajax call (using post())
* implement expiring events
* implement scrolling /browse events
* add un-join button to /user
* sort events by # of people attending
* clicking on a comment always erases, should fix this
* add editing events
  -- extrapolate existing /create UI to have hooks for populating w/ data
* Make a FB login  w/ logo? (see: http://www.letsdrinktonight.com)
* Overhaul day / times
  - check for string recognition
    -- should recognize string 'today' as datetime.date.today(), etc.
  - implement date and time ranges(i think they just subtract?)

BUGS:
------------
- When a user isn't logged in but then goes to join an event, logs in,
  and then he's already going to that event, it just lands at an empty
  screen (is it a python if statement?)
- When a user isn't logged in but wants to make a hangout, it nukes
  their hangout info before logging them back in


Not Urgent
_____________
Add datepicker
Add YQL alternative from Thriftfish (for geolocating)
When there are no hangouts in /browse, add a 'create' message
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


###########################################################################################

DONE
-------------
- When a user who's logged in before, logs in again- their data (likes,pic) gets nuked
* pair down /create fields
* add event comments
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

Fix alignment issue w/ logo
Break DeleteHandler into tasks
Add a number system for people who are going to an event
Fix security hole for directly accessing *.html files
Change default-value in forms to change depending on FOCUS not on click
Auto-Join people who create an event
Change create() to redirect to event template
Create event template

[Add Facebook (http://developers.facebook.com/docs/reference/api/)]

'''

import os
import logging
import datetime
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.api import taskqueue
from models import *
from fb.oauth import *

class FAQPage(BaseHandler):
    def get(self):
        user = self.current_user
        self.response.out.write(template.render('static/temp.html',
                                                {'linktext':'My Hangouts' if user else 'Login'}))

class AboutPage(BaseHandler):
    def get(self):
        user = users.get_current_user()
        self.response.out.write(template.render('static/temp.html',
                                                {'linktext':'My Hangouts' if user else 'Login'}))

class EventPurge(BaseHandler):
    # Takes an event by key and removes itself from all its members
    def post(self):
        eventKey = self.request.get('key')
        event = db.get(eventKey)

        for event_member in event.members:
            taskqueue.add(url="/unjointask", params={'userKey': event_member,
                                                     'eventKey': eventKey})
            # step 2. delete the group itself
            taskqueue.add(url="/deletetask", params={'key': eventKey})
        
class DeleteTask(BaseHandler):
    # Takes a key and deletes its corresponding entity
    def post(self):
        db.delete(self.request.get('key'))
        
class UnjoinTask(BaseHandler):
    # Takes an event and user
    # removes the user from the given event
    def post(self):
        member = db.get(self.request.get('userKey'))
        member.events = [s for s in member.events if str(s) != self.request.get('eventKey')]
        member.put()

class Join(BaseHandler):
    def get(self):
        current_user = users.get_current_user()
        if current_user:
            key = self.request.get('key')
            event = db.get(key)
            user = db.GqlQuery("SELECT * FROM User WHERE user_id = '%s'" %
                               users.get_current_user().user_id()).get()
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
                                    last_date = now,
                                    events = [event.key()])
                user_profile.put()
                event.members.append(user_profile.key())
                event.put()
                self.redirect('/user')
        else:
            self.redirect(users.create_login_url(self.request.uri))

class EventPage(BaseHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            existing_user = db.GqlQuery("SELECT * FROM User WHERE user_id = '%s'" %
                                        user.user_id()).get()
        else:
            existing_user = None
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
                           'posts': [db.get(p) for p in event.posts],
                           'join_button': False if existing_user and existing_user.key() in event.members else True}
        self.response.out.write(template.render('static/event.html', template_values))

    def post(self):
        current_user = users.get_current_user()
        if current_user: # Make sure user is logged in
            existing_user = db.GqlQuery("SELECT * FROM User WHERE user_id = '%s'" %
                                        current_user.user_id()).get()
            key = self.request.get('event_key')
            current_event = db.get(key)
            comment_content = self.request.get('comment_content') 
            comment = Post(author = current_user,
                           content = comment_content,
                           event = current_event)
            comment.put()
            comment_key = comment.key()
            current_event.posts.append(comment_key)
            current_event.put()
            self.redirect("/event?key=%s" % current_event.key())
        else:
            self.redirect(users.create_login_url(self.request.uri))
	
class LogoPage(BaseHandler):
    def get(self):
        self.response.out.write(template.render('static/logo.html', {}))

class MainPage(BaseHandler):
    def get(self):
        linktext = 'My Hangouts' if users.get_current_user() else 'Login'
        events = db.GqlQuery("SELECT * FROM Event LIMIT 100")
        template_values = {'linktext': linktext,
                           'events': events}
        self.response.out.write(template.render('static/index.html', template_values))

class Browse(BaseHandler):
    def get(self):
        linktext = 'My Hangouts' if users.get_current_user() else 'Login'
        events = db.GqlQuery("SELECT * FROM Event LIMIT 100")
        template_values = {'linktext': linktext,
                           'events': events}
        self.response.out.write(template.render('static/browse.html', template_values))
        
class CreatePage(BaseHandler):
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
            existing_user = db.GqlQuery("SELECT * FROM User WHERE user_id = '%s'" %
                                        current_user.user_id()).get()
            now = datetime.datetime.now()
            time = self.request.get('time')
            date = self.request.get('date')
            if existing_user:
                event = Event(creator = current_user,
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
                                    last_date = now)
                user_profile.put()
                event = Event(creator = current_user,
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

class UserPage(BaseHandler):
    def get(self):
        user = self.current_user
        if user:
            # If stored profile is > 3 days old, update it
            if (datetime.now() - user.updated).days > 3:
                logging.info('INFO: FB data is not fresh; requesting new')
                FBUpdateHandler(user).load()

            # Render /user Page
            events = [db.get(event) for event in user.events] if user else []
            template_values = {'current_user': user,
                               'logout': users.create_logout_url("/"),
                               'linktext': 'My Hangouts',
                               'events': events}
            self.response.out.write(template.render('static/user.html', template_values))
            self.response.out.write('<p><a href="/auth/logout">Log out</a></p>')
        else:
            self.redirect('/auth/login')
            
        """
        ## IMAGES

        # Display user's profile pic w/ appropriate headers
        picture = user.picture
        self.response.headers['Content-Type'] = 'image/jpeg'
        self.response.out.write(picture)

        # Display user's profile pic from FB
        self.response.out.write(template.render(path, args))
        self.response.out.write('<img src="http://graph.facebook.com/%s/picture"/>' % self.current_user.id)
        """

class Geo(webapp.RequestHandler):
    def get(self):    
        self.response.out.write(template.render('static/geo.html', {}))
