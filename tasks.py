import webapp2
import os
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.api import memcache
from google.appengine.api import mail

import logging
import models
import datetime
from models import Player
from models import GameDate
from common import *

class UpdateGameHandler(webapp2.RequestHandler):
	def get(self):
		updateCurrentGames()
		
app = webapp2.WSGIApplication([
	('/tasks/updateGames', UpdateGameHandler),
], debug=True)