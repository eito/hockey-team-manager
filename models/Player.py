from google.appengine.ext import db
from google.appengine.api import users

class Player(db.Model):
	"""Object representing a player for Esri Hockey"""
	fname = db.StringProperty()
	lname = db.StringProperty()
	email = db.EmailProperty()
	goalie = db.BooleanProperty()
	inThisWeek = db.BooleanProperty()
	sub = db.BooleanProperty()
	team = db.StringProperty()
	phone = db.PhoneNumberProperty()
	
	def full_name():
		return self.fname + " " + self.lname
	
	def toJson(self):
		json = {}
		json['fname'] = self.fname
		json['lname'] = self.lname
		json['email'] = self.email
		json['goalie'] = 'true' if self.goalie else 'false'
		json['inThisWeek'] = 'true' if self.inThisWeek else 'false'
		json['sub'] = 'true' if self.sub else 'false'
		json['team'] = self.team if self.team != "" else None
		json['phone'] = self.phone if self.phone else None
		return json
		