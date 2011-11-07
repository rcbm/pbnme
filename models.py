from google.appengine.ext import db
from google.appengine.api import users

class fbUser(db.Model):
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    id = db.StringProperty(required=True)
    name = db.StringProperty(required=True)
    email = db.EmailProperty(default=None)    # How do we get this?
    profile_url = db.StringProperty(required=True)
    access_token = db.StringProperty(required=True)
    picture = db.BlobProperty(default=None)
    likes = db.StringListProperty(default=None)
    events = db.ListProperty(db.Key)

    
class Event(db.Model):
    created = db.DateTimeProperty(auto_now_add=True, default=None)
    updated = db.DateTimeProperty(auto_now=True)
    title = db.StringProperty(default=None, required=True)
    active = db.BooleanProperty(default=True)
    creator = db.ReferenceProperty(fbUser)
    datetime = db.DateTimeProperty(default=None, required=True)
    location = db.StringProperty(default=None)
    members = db.ListProperty(db.Key)
    posts = db.ListProperty(db.Key)

    
class Post(db.Model):
    created = db.DateTimeProperty(auto_now_add=True)
    event = db.ReferenceProperty(Event)
    author = db.ReferenceProperty(fbUser)
    content = db.StringProperty(default=None, required=True, multiline=True)
