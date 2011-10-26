from google.appengine.ext import db
from google.appengine.api import users

class fbUser(db.Model):
    id = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    name = db.StringProperty(required=True)
    profile_url = db.StringProperty(required=True)
    access_token = db.StringProperty(required=True)
    picture = db.BlobProperty(default=None)
    likes = db.StringListProperty(default=None)
    
class User(db.Model):
    user = db.UserProperty(required=True)
    user_id = db.StringProperty(default=None, required=True)
    email = db.EmailProperty(default=None, required=True)
    create_date = db.DateTimeProperty(default=None, required=True)
    last_date = db.DateTimeProperty(default=None, required=True)
    events = db.ListProperty(db.Key)
    
class Event(db.Model):
    create_date = db.DateTimeProperty(default=None, required=True)
    creator = db.UserProperty()
    datetime = db.DateTimeProperty(default=None, required=True)
    title = db.StringProperty(default=None, required=True)
    location = db.StringProperty(default=None)
    description = db.StringProperty(default=None, required=False, multiline=True)
    members = db.ListProperty(db.Key)
    posts = db.ListProperty(db.Key, default=None)
    
class Post(db.Model):
    author = db.UserProperty()
    content = db.StringProperty(default=None, required=True, multiline=True)
    create_date = db.DateTimeProperty(auto_now_add=True)
    event = db.ReferenceProperty()

