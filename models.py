from google.appengine.ext import db
from google.appengine.api import users

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
    description = db.StringProperty(default=None, required=True, multiline=True)
    members = db.ListProperty(db.Key)
    