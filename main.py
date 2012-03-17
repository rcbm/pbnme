'''
- Implement matching
  - Store a copy of a person's likes
  - Iterate through a person's friendslist and store their likes as well
    ie. {'1223459': [like1, like2, like3], ...}

    GOAL: predict if two people would be friends.
    METHOD: for each person, compare their friends to them and use that as a thing
    
- Implement geocoding
  - Should use matt's geocoding code as first pass
  - Should geocode w/ google as second pass, store it in users's account

- Overhaul times
  - 'Noon','Midnight','Today','Tomorrow' should be parsed correctly
  - JS should send the users' time via the POST method ; date()
    * Local machine time is compared to JS time. The difference is used
      to compute the 'computed time' (in UTC or wherever) and stored, for 
      notifications and whatnot.
    - default should not go to midnight but rather not have a time

Google Prediction API
- http://code.google.com/apis/predict/

HTML BUGS
------------------------
- when not logged in, clicking 'ill come' just sends to /user but doesnt join
- footer index.html
- show people who are going


Features
-------------------------
FRIEND FOLLOWING:


GEOLOCATION:
Users in Berkeley CA and Pittsburgh PA can log in and create events.
Users in other places can only see events but cannot create or join them.
If they try they'll get a polite message and a promise we'll contact them
when its available in their city.
QUICK N DIRTY: We have HTML5 code that works, need to test YQL backup code.
Maybe Impliment this on /auth/login? 

SORTING EVENTS:
Users want to sort events by date, # of users, other things.
QUICK N DIRTY: Research GQL 'sort by' commands


EVENT NOTIFICATIONS:
Users want to be notified of their event via email
QUICK N DIRTY: 


EVENT SHARING:
Events should opt-out share w/ friends (like on fb, twitter, etc.)
QUICK N DIRTY: 


###############################################


THINGS TO-DO:

URGENT
-------------
* Add 'Blog' to footers
* / should sort by newest events? # of people going? What?
* Add 'start' button to /
* implement email and/or fb message reminders
* Seperate Day and / TIME in /events
* make more robust /browse (sort by date, sort by score, etc.)
* add sorting of events by # of people attending
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
- "noon" goes to midnight

Not Urgent
_____________
implement /join as an ajax call (using post())
Add optional 'Description' field
Add datepicker
Add existing group checking for create()
Implement 'default-value' checking to create form in JS
Make a safe-guard that if manually deleting an event (on the backend),
  the reference in the user-profiles is also deleted... maybe when a user loads their page?
When a person puts their "house" in, we should pull their approximate address.

Harder:
-------------
[implement form validation w/ js and python]
[Add uploading of a photo when creating a hangout]
[Add Geolocation (http://diveintohtml5.org/geolocation.html)]


###########################################################################################

DONE
-------------
- Kludge = 3 hour subtraction for time rather than actual timezone comparison

'''

import os
import logging
from datetime import datetime,timedelta
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.api import taskqueue
from models import *
from fb.oauth import *

class RefreshTask(BaseHandler):
    # Takes a key and loads FB Profile Info
    # Should only be run if now() - last > 72hrs
    def post(self):
        key = self.request.get('key')
        user = db.get(key)
        logging.info('INFO: %s - %s  Attempting to update profile' % (user.id, user.name))
        graph = facebook.GraphAPI(user.access_token)

        # Download Email
        profile = graph.get_object("/me")
        user.email = str(profile['email'])
        
        # Download Likes
        likes = graph.get_object("/me/likes")
        likes = likes['data']
        user.likes = [like['id'] for like in likes]
        
        # Download Picture
        picture = urllib2.urlopen('http://graph.facebook.com/%s/picture' % user.id).read()
        user.picture = db.Blob(picture)
        user.updated = datetime.now()
        user.put()
        logging.info('INFO: %s - %s  Update Complete' % (user.id, user.name))

        
class ExpireTask(BaseHandler):
    # Takes a key and flips the active bit of the corresponding entity
    def post(self):
        event = db.get(self.request.get('eventKey'))
        event.active = False
        event.put()


class ExpireDaemon(BaseHandler):
    # Looks for 100 events that are in the past and are still flagged as active
    def get(self):
        now = str(datetime.now() - timedelta(hours=5)).split('.')[0]
        events = db.GqlQuery("SELECT * FROM Event WHERE datetime < DATETIME('%s') AND active=True LIMIT 100" % now)
        for e in events:
            logging.info('INFO: Deactivating event: %s' % e.key())
            taskqueue.add(url="/expiretask", params={'eventKey': e.key()})
            
        
class FAQPage(BaseHandler):
    def get(self):
        user = self.current_user
        self.response.out.write(template.render('static/faq.html', { 'linktext': self.linktext }))

        
class AboutPage(BaseHandler):
    def get(self):
        user = self.current_user
        self.response.out.write(template.render('static/about.html', { 'linktext': self.linktext }))

class EventPurge(BaseHandler):
    # Takes an event by key and removes itself from all its members
    def post(self):
        eventKey = self.request.get('key')
        event = db.get(eventKey)
        for event_member in event.members:
            taskqueue.add(url="/unjointask", params={'scores': [29, 53, 75, 92, 31],
                                                     'userKey': event_member,
                                                     'eventKey': eventKey})
            # step 2. delete the group itself
            taskqueue.add(url="/deletetask", params={ 'key': eventKey })
            
        
class DeleteTask(BaseHandler):
    # Takes a key and deletes its corresponding entity
    def post(self):
        db.delete(self.request.get('key'))

        
class Unjoin(BaseHandler):
    # Takes an event and removes the user from it
    def get(self):
        user = self.current_user
        event = db.get(self.request.get('key'))
        event.members = [s for s in event.members if str(s) != str(user.key())]
        if len(event.members) < 1:
            logging.info('Event %s - %s has no members, deleting' %(event.key(), event.title))
            db.delete(event)
            user.events = [s for s in user.events if str(s) != self.request.get('key')]
            user.put()
        else:
            user.events = [s for s in user.events if str(s) != self.request.get('key')]
            user.put()
            event.put()
            
        self.redirect('/user')

        
class UnjoinTask(BaseHandler):
    #### SHOULD THIS GO BACK TO THE EVENTS AND REMOVE THE USER FROM THE LIST?
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

            
class Browse(BaseHandler):
    def get(self):
        weekdays = ['Mon.', 'Tues.', 'Wed.', 'Thurs.', 'Fri.', 'Sat.', 'Sun.',]
        now = str(datetime.now() - timedelta(hours=5)).split('.')[0]
        events = db.GqlQuery("SELECT * FROM Event WHERE datetime > DATETIME('%s') AND active=True LIMIT 100" % now)
        self.response.out.write(template.render('static/browse.html', { 'linktext': self.linktext,
                                                                        'events': events }))
class Hunch(BaseHandler):
    def get(self):
        '''
        url = 'http://api.hunch.com/api/v1/get-recommendations/?user_id=fb_rogercosseboom&topic_ids=list_movie&limit=10'
        from django.utils import simplejson as json
        thing = json.load(urllib2.urlopen(url))
        self.response.out.write([s['title'] for s in thing['recommendations']])
        '''
        self.response.out.write(template.render('static/hunch.html', {}))
        #self.redirect('http://www.hunch.com/authorize/v1?app_id=3147164&next=http://holy-mountain.appspot.com/')

        
class Future(BaseHandler):
    def get(self):
        weekdays = ['Mon.', 'Tues.', 'Wed.', 'Thurs.', 'Fri.', 'Sat.', 'Sun.',]
        now = str(datetime.now() - timedelta(hours=5)).split('.')[0]
        events = db.GqlQuery("SELECT * FROM Event WHERE datetime > DATETIME('%s') AND active=True LIMIT 100" % now)
        self.response.out.write(template.render('static/future.html', { 'linktext': self.linktext,
                                                                        'events': events }))

class Score(BaseHandler):
    def get(self):
        from random import randrange
        now = str(datetime.now() - timedelta(hours=5)).split('.')[0]
        events = db.GqlQuery("SELECT * FROM Event WHERE datetime > DATETIME('%s') AND active=True LIMIT 100" % now)
        for event in events:
            event.score = randrange(0 ,100)
            print '%s - %s' %(event.title, event.score)
            event.put()

            
class EventPage(BaseHandler):
    def get(self):
        weekdays = ['Mon.', 'Tues.', 'Wed.', 'Thurs.', 'Fri.', 'Sat.', 'Sun.',]
        user = existing_user = self.current_user
        key = self.request.get('key')
        event = db.get(key)
        time = event.datetime.time()
        date = '%s/%s' %(event.datetime.month, event.datetime.day)
        members = [db.get(key) for key in event.members]
        editable = False if user and user.key() != event.creator.key() else True
        join_button = False if existing_user and existing_user.key() in event.members else True
        self.response.out.write(template.render('static/event.html', { 'weekday': weekdays[event.datetime.weekday()],
                                                                       'event': event,
                                                                       'members': members,
                                                                       'time': time,
                                                                       'date': date,
                                                                       'editable': editable,
                                                                       'linktext': self.linktext,
                                                                       'key': event.key(),
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
        now = str(datetime.now() - timedelta(hours=5)).split('.')[0]
        events = db.GqlQuery("SELECT * FROM Event WHERE datetime > DATETIME('%s') AND active=True LIMIT 100" % now)
        self.response.out.write(template.render('static/index.html', { 'linktext': self.linktext,
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

            
class EditPage(BaseHandler):
    def get(self):
        user = self.current_user
        event = db.get(self.request.get('event'))
        self.response.out.write(template.render('static/edit.html', { 'event': event,
                                                                      'linktext': self.linktext }))
    def post(self):
        user = self.current_user
        if user:
            event = db.get(self.request.get('key'))
            from dateutil import parser
            event.title = self.request.get('title')
            event.location = location = self.request.get('location')
            time = self.request.get('time')
            date = self.request.get('date')
            event.datetime = parser.parse('%s %s' %(date, time), fuzzy=True)
            event.put()
            self.redirect("/event?key=%s" % event.key())
        else:
            self.redirect('/auth/login')

            
class ProfilePic(BaseHandler):
    def get(self):
        picture = db.get(self.request.get('key')).picture
        self.response.headers['Content-Type'] = 'image/jpeg'
        self.response.out.write(picture)
        
        
class UserPage(BaseHandler):
    def get(self):
        user = self.current_user
        if user:
            # If stored profile is > 3 days old, update it in the background
            if (datetime.now() - user.updated).days > 3:
                logging.info('INFO: %s - %s  FB data is not fresh; Requesting New' % (user.id, user.name))
                taskqueue.add(url="/refresh", params={'key': str(user.key())})
            
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
