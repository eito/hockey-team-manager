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

class MondayMailHandler(webapp2.RequestHandler):
	def get(self):
		games = memcache.get('gamedates')
		if not games:
			games = GameDate.all()
			games.order('date')
		game = games[0]
		players = memcache.get('players')
		if not players:
			players = Player.all()
			players.order('lname')
			players.order('fname')
			memcache.set('players', players)
		to_list = []
		for player in players:
			if not player.sub:
				to_list.append(player.email)
		email_sender = "Esri Hockey <hockeyesri@gmail.com>"
		email_subject = "Esri Hockey - %d/%d/%d" % (game.date.month, game.date.day, game.date.year)
		email_body = """Head on over to http://esrihockey.appspot.com to let us know if you are in or out."""		
		if not game.isThisWeek():
			logging.info("NOT GAME THIS WEEK")
			email_subject = "Esri Hockey - No Game This Week"
			email_body = """Reminder we are off this week. Our next game will be %d/%d/%d.""" % (game.date.month, game.date.day, game.date.year)
		mail.send_mail(sender=email_sender, to=to_list, subject=email_subject, body=email_body)
		
app = webapp2.WSGIApplication([
	('/mail/weekly', MondayMailHandler),
], debug=True)