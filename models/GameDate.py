from google.appengine.ext import db
import json
import datetime
import time
from pst import Pacific_tzinfo

def localTime():
	return datetime.datetime.fromtimestamp(time.mktime(datetime.datetime.utcnow().timetuple()), Pacific_tzinfo())

class GameDate(db.Model):
	"""Object representing a GameDate for Esri Hockey"""
	date = db.DateTimeProperty()
	time = db.StringProperty()
			
	def isThisWeek(self):
		if int(self.date.strftime("%U")) == int(localTime().strftime("%U")):
			return True
		else:
			return False
	
	def toJson(self):
		json = {}
		json['year'] = self.date.year
		json['month'] = self.date.month
		json['day'] = self.date.day
		json['time'] = self.time
		return json