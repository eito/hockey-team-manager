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

def sendEmailToPlayer(email_sender, email_to, email_subject, email_body):
	mail.send_mail(sender=email_sender, to=email_to, subject=email_subject, body=email_body)

class AdminRosterHandler(webapp2.RequestHandler):
	def get(self):
		players = memcache.get('players')
		if not players:
			logging.info("no players in cache")
			players = Player.all()
			players.order("lname")
			players.order("fname")
			memcache.set('players', players)
		skaters = []
		goalies = []
		for player in players:
			if player.inThisWeek:
				if player.goalie:
					goalies.append(player)
				else:
					skaters.append(player)
		values = {"goalies":goalies, "skaters":skaters}
		path = os.path.join(os.path.dirname(__file__), 'templates/edit_rosters.html')
		self.response.out.write(template.render(path, values))

class SubmitRosterHandler(webapp2.RequestHandler):
	def post(self):
		players = memcache.get('players')
		if not players:
			players = Player.all()
		if players:
			for player in players:
				if player.inThisWeek:
					team = self.request.get("""blueOrWhite%d""" % player.key().id())
					logging.info("team: %s", team)
					if team == "blue" or team == "white":
						player.team = team
						player.put()
		memcache.set('players', players)
		results = db.GqlQuery('SELECT * FROM GameDate ORDER BY date ASC')
		game = results.fetch(1)[0]
		subject = """Esri Hockey Rosters for %d/%d/%d""" % (game.date.month, game.date.day, game.date.year)
		finalize = self.request.get("finalize")		
		if finalize:
			email_body = self.request.get('email_body')
			if email_body == "":
				email_body = """Rosters for Esri Hockey are available at: http://esrihockey.appspot.com/rosters"""
			else:
				appendText = """Rosters for Esri Hockey are available at: http://esrihockey.appspot.com/rosters"""
				email_body = email_body + "\n\n%s" % appendText
			email_to_list = GetEmailListAllIn()
			mail.send_mail(sender="Esri Hockey <hockeyesri@gmail.com>",
			to=email_to_list,
			subject=subject,
			body=email_body)
		values = { "message" : "Changes have been saved successfully."}
		path = os.path.join(os.path.dirname(__file__), 'templates/admin_success.html')
		self.response.out.write(template.render(path, values))		
	
class EmailHandler(webapp2.RequestHandler):
	def get(self):
		values = { }
		path = os.path.join(os.path.dirname(__file__), 'templates/email.html')
		self.response.out.write(template.render(path, values))
	
	def post(self):
		regulars = self.request.get('regulars')
		subs = self.request.get('subs')
		players = memcache.get('players')		
		if not players:
			players = Player.all()
			players.order("lname")
			players.order("fname")
			memcache.set("players", players)
			
		email_sender = "Esri Hockey <hockeyesri@gmail.com>"
		allRegulars = self.request.get('allRegulars')
		allSubs = self.request.get('allSubs')	
		email_to = GetEmailList(regulars=allRegulars, subs=allSubs)
		logging.info(email_to)
		email_subject = self.request.get("subject")
		email_body = self.request.get("body")
		if len(email_to) < 1:
			values = { "message" : "Specify regulars or subs.", "email_body":email_body, "email_subject":email_subject}
			path = os.path.join(os.path.dirname(__file__), 'templates/email.html')
			self.response.out.write(template.render(path, values))
			return
		#for player in players:
		#	if player.inThisWeek:
		#		if regulars and not player.sub:
		#			mail.send_mail(sender=email_sender, to=player.email, subject=email_subject, body=email_body)
		mail.send_mail(sender=email_sender, to=email_to, subject=email_subject, body=email_body)

class ResetRosterHandler(webapp2.RequestHandler):
	def get(self):
		players = Player.all()
		for player in players:
			player.team = None
			player.put()
		values = { "message" : "Rosters have been reset."}
		path = os.path.join(os.path.dirname(__file__), 'templates/admin_success.html')
		self.response.out.write(template.render(path, values))

class ResetInOutHandler(webapp2.RequestHandler):
	def get(self):
		players = Player.all()
		for player in players:
			player.inThisWeek = False
			player.team = None
			player.put()
		values = { "message" : "Players have been reset to no team and 'out'."}
		path = os.path.join(os.path.dirname(__file__), 'templates/admin_success.html')
		self.response.out.write(template.render(path, values))
			
app = webapp2.WSGIApplication([
	('/admin/rosters', AdminRosterHandler),
	('/admin/rosters/submit', SubmitRosterHandler),
	('/admin/email', EmailHandler),
	('/admin/rosters/reset', ResetRosterHandler),
	('/admin/inout/reset', ResetInOutHandler),
], debug=True)