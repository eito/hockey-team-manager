from google.appengine.ext import db
from google.appengine.api import users

class Comment(db.Model):
	"""Object representing a comment for Esri Hockey"""
	text = db.TextProperty()
	name = db.StringProperty()
	time = db.DateTimeProperty()