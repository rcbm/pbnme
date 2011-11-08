'''
Future Sketches
-------------------------
GEOLOCATION:
Users in Berkeley CA and Pittsburgh PA can log in and create events.
Users in other places can only see events but cannot create or join them.
If they try they'll get a polite message and a promise we'll contact them
when its available in their city.


FB QUESTIONS:
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


###############################################


THINGS TO-DO:

URGENT
-------------
# LOOK UP BATCH put()'s for /create
# LOOK UP SEPERATING DAY / TIME in /events
* add content to FAQ (hook already made)
* add content to About (hook already made)
* implement email and/or fb message reminders
* make more robust /browse (sort by date, sort by score, etc.)
* implement /join as an ajax call (using post())
* implement expiring events
* implement scrolling /browse events
* add un-join button to /user
* sort events by # of people attending
* add editing events
  -- extrapolate existing /create UI to have hooks for populating w/ data
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
Add flipping words for group on homepage (circle, group, crew, posse, gang, etc...)
Add optional 'Description' field
Add datepicker
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
- Deleting one's hangouts seems broken
* swap Google Users to FB
- When a user who's logged in before, logs in again- their data (likes,pic) gets nuked
[Add Facebook (http://developers.facebook.com/docs/reference/api/)]
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
* clicking on a comment always erases, should fix this
* Make a FB login  w/ logo? (see: http://www.letsdrinktonight.com)
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
        self.response.out.write(template.render('static/faq.html', {'linktext': self.linktext}))

class AboutPage(BaseHandler):
    def get(self):
        user = self.current_user
        self.response.out.write(template.render('static/about.html', {'linktext': self.linktext}))

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
        user = self.current_user
        if user:
            key = self.request.get('key')
            event = db.get(key)
            # Make sure user isn't already part of the event
            if user.key() not in event.members:
                user.events.append(db.Key(key))
                user.put()
                event.members.append(user.key())
                event.put()
                self.redirect('/user')
        else:
            self.redirect('/auth/login')

            
class EventPage(BaseHandler):
    def get(self):
        user = existing_user = self.current_user
        key = self.request.get('key')
        event = db.get(key)
        join_button = False if existing_user and existing_user.key() in event.members else True
        self.response.out.write(template.render('static/event.html', { 'linktext': self.linktext,
                                                                       'key': event.key(),
                                                                       'title': event.title,
                                                                       'location': event.location,
                                                                       'datetime': event.datetime,
                                                                       'members': [db.get(m) for m in event.members],
                                                                       'posts': [db.get(p) for p in event.posts],
                                                                       'join_button': join_button}))

    def post(self):
        current_user = existing_user = self.current_user
        # Make sure user is logged in
        if current_user: 
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
            self.redirect('/auth/login')

            
        
class MainPage(BaseHandler):
    def get(self):
        self.response.out.write(template.render('static/index.html', { 'linktext':self.linktext }))

        
class NewMainPage(BaseHandler):
    def get(self):
        events = db.GqlQuery("SELECT * FROM Event LIMIT 100")
        self.response.out.write(template.render('static/index2.html', { 'linktext': self.linktext,
                                                                        'events': events }))


class Browse(BaseHandler):
    def get(self):
        events = db.GqlQuery("SELECT * FROM Event LIMIT 100")
        self.response.out.write(template.render('static/browse.html', { 'linktext': self.linktext,
                                                                        'events': events }))

        
class CreatePage(BaseHandler):
    def get(self):
        self.response.out.write(template.render('static/create.html', {'linktext': self.linktext}))
        
    def post(self):
        user = self.current_user
        if user:
            from dateutil import parser
            title = self.request.get('title')
            location = self.request.get('location')
            now = datetime.now()
            time = self.request.get('time')
            date = self.request.get('date')
            event = Event(creator = user,
                          title = title,
                          location = location,
                          datetime = parser.parse('%s %s' %(date, time), fuzzy=True),
                          members = [user.key()])
            event.put()
            user.events.append(event.key())
            user.put()
            self.redirect("/event?key=%s" % event.key())
        else:
            self.redirect('/auth/login')

            
class UserPage(BaseHandler):
    def get(self):
        user = self.current_user
        if user:
            # If stored profile is > 3 days old, update it
            if (datetime.now() - user.updated).days > 3:
                logging.info('INFO: FB data is not fresh; requesting new')
                FBUpdateHandler(user).load()

            # Render /user Page
            events = [db.get(event) for event in user.events]
            self.response.out.write(template.render('static/user.html', { 'linktext': self.linktext,
                                                                          'current_user': user,
                                                                          'events': events }))
        else:
            self.redirect('/auth/login')
            
        """
        ## IMAGES STUFF

        # Display user's profile pic w/ appropriate headers
        picture = user.picture
        self.response.headers['Content-Type'] = 'image/jpeg'
        self.response.out.write(picture)
        """

        
class Geo(BaseHandler):
    def get(self):    
        self.response.out.write(template.render('static/geo.html', {}))
