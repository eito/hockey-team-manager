#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import os
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.api import memcache

import logging
import models
import datetime
import time
from models import Player
from models import GameDate
from models import Comment
from pst import Pacific_tzinfo
from common import *

class SubsHandler(webapp2.RequestHandler):
	def get(self):
		subs = GetAllSubs()
		values = {}
		if subs:
			values = {'subs':subs}
		path = os.path.join(os.path.dirname(__file__), 'templates/subs.html')
		self.response.out.write(template.render(path, values))
		
class MainHandler(webapp2.RequestHandler):
    def get(self):
		#results = db.GqlQuery('SELECT * FROM GameDate ORDER BY date ASC')
		#game = results.fetch(1)[0]
		game = GetNextGame()
		# we need to pass in a game, goalies array, players array
		#results = Player.all()
		results = GetAllPlayers()
		inGoalies = []
		inPlayers = []
		outPlayers = []
		for player in results:
			if player.inThisWeek:
				if player.goalie:
					inGoalies.append(player)
				else:
					inPlayers.append(player)
			else:
				outPlayers.append(player)
		inPlayerMap = map(None, inPlayers, inGoalies)
		comments = Comment.all()
		comments.order("-time")
		values = {"game" : game, "inPlayerMap":inPlayerMap, "outPlayers":outPlayers, "comments":comments, "numGoalies": len(inGoalies), "numSkaters":len(inPlayers)}
		path = os.path.join(os.path.dirname(__file__), 'templates/main.html')
		self.response.out.write(template.render(path, values))
		
class RosterHandler(webapp2.RequestHandler):
    def get(self):
		game = GetNextGame()
		blue = {}
		white = {}
		#results = db.GqlQuery('SELECT * FROM Player ORDER BY lname DESC').fetch(100)
		results = GetAllPlayers()
		blueSkaters = []
		blueGoalies = []
		whiteSkaters = []
		whiteGoalies = []
		# figure out who is in/out
		for player in results:
			if player.inThisWeek:
				if player.team == "blue":
					if player.goalie:
						blueGoalies.append(player)
					else:
						blueSkaters.append(player)
				elif player.team == "white":
					if player.goalie:
						whiteGoalies.append(player)
					else:
						whiteSkaters.append(player)
		whitePlayerMap = map(None, whiteSkaters, whiteGoalies)
		bluePlayerMap = map(None, blueSkaters, blueGoalies)
		values = {"game" : game, "bluePlayerMap":bluePlayerMap, "whitePlayerMap":whitePlayerMap}
		path = os.path.join(os.path.dirname(__file__), 'templates/rosters.html')
		self.response.out.write(template.render(path, values))

class PlayersHandler(webapp2.RequestHandler):
	def get(self):
		players = GetAllPlayers()
		values = { "players" : players}
		path = os.path.join(os.path.dirname(__file__), 'templates/players.html')
		self.response.out.write(template.render(path, values))
		
def RenderSignupPage(fname, lname, email, message, phone):
	values = { "fname": fname, "lname": lname, "email":email, "message":message, "phone":phone}
	path = os.path.join(os.path.dirname(__file__), 'templates/signup.html')
	return template.render(path, values)
	
class SignupHandler(webapp2.RequestHandler):
	def get(self):
		self.response.out.write(RenderSignupPage("", "", "", "", ""))

	def post(self):
		first_name = self.request.get("fname")
		last_name = self.request.get("lname")		
		email_address = self.request.get("email")
		phone_number = self.request.get("phone")
		if phone_number == "":
			phone_number = None
		if first_name == "" or last_name == "" or email_address == "":
			self.response.out.write(RenderSignupPage(first_name, last_name, email_address,"Fill in all the fields", phone_number))
		else:
			memcache.delete('players')
			player = Player(fname=first_name, lname=last_name, email=email_address, goalie=False, rating=0, phone=phone_number)
			player.put()
			values = { "message":"Thank you for signing up!"}
			path = os.path.join(os.path.dirname(__file__), 'templates/success.html')
			self.response.out.write(template.render(path, values))
		
class ScheduleHandler(webapp2.RequestHandler):
	def get(self):
		self.response.write('This is where the schedule would be.')

class PlayerEditHandler(webapp2.RequestHandler):
	def get(self):
		players = GetAllPlayers()
		values = { "players" : players}
		path = os.path.join(os.path.dirname(__file__), 'templates/edit_players.html')
		self.response.out.write(template.render(path, values))
	
	def post(self):
		players = GetAllPlayers()
		if players:
			for player in players:
				player.fname = self.request.get("""fname%d""" % player.key().id())
				player.lname = self.request.get("""lname%d""" % player.key().id())
				player.email = self.request.get("""email%d""" % player.key().id())
				phone = self.request.get("""phone%d""" % player.key().id())
				if phone:
					player.phone = phone
				player.rating = int(self.request.get("""rating%d""" % player.key().id()))				
				player.put()
		memcache.set('players', players)		
		values = { "message" : "Changes have been saved successfully."}
		path = os.path.join(os.path.dirname(__file__), 'templates/success.html')
		self.response.out.write(template.render(path, values))	

class PlayerHandler(webapp2.RequestHandler):
	def get(self, playerId):		
		player = Player.get_by_id(int(playerId))
		if player:
			values = {"player":player}
			path = os.path.join(os.path.dirname(__file__), 'templates/edit_player.html')			
		else:
			values = { "message" : "Error finding player."}
			path = os.path.join(os.path.dirname(__file__), 'templates/success.html')
		self.response.out.write(template.render(path, values))
	
	def post(self, playerId):
		deleteClicked = self.request.get("delete")
		player = Player.get_by_id(int(playerId))
		if player:
			if deleteClicked:
				player.delete()
				values = { "message" : "Player deleted successfully."}
			else:	
				#TODO: optimize this... if values are equal, don't post
				player.fname = self.request.get("fname%s" % playerId)
				player.lname = self.request.get("lname%s" % playerId)
				player.email = self.request.get("email%s" % playerId)
				phone = self.request.get("phone%s" % playerId)
				if phone:
					player.phone = phone
				inOrOut = self.request.get("inOrOut")
				if inOrOut == "in":
					player.inThisWeek = True
				else:
					player.inThisWeek = False
				playerType = self.request.get("playerType")
				logging.info(playerType)
				if playerType == "goalie":
					player.goalie = True
				else:
					player.goalie = False
				regularOrSub = self.request.get("regularOrSub")
				if regularOrSub == "sub":
					player.sub = True
				else:
					player.sub = False
				player.put()
				memcache.delete('players')
				values = { "message" : "Changes have been saved successfully."}
		else:
			values = { "message" : "Error finding player."}
		path = os.path.join(os.path.dirname(__file__), 'templates/success.html')
		self.response.out.write(template.render(path, values))

def RenderAddDatePage(month, day, year, time, message):
	values = { "message":message}
	path = os.path.join(os.path.dirname(__file__), 'templates/add_gamedate.html')
	return template.render(path, values)
	
class AddCommentHandler(webapp2.RequestHandler):
	def get(self):
		values = {}
		path = os.path.join(os.path.dirname(__file__), 'templates/add_comment.html')
		self.response.out.write(template.render(path, values))
	
	def post(self):
		commentText = self.request.get("comment")
		nameText = self.request.get("name")
		#time = datetime.now()
		comment = Comment(text=commentText, name=nameText, time=localTime())
		comment.put()
		self.redirect("/")
		
class AddGameDateHandler(webapp2.RequestHandler):
	def get(self):
		self.response.out.write(RenderAddDatePage("", "", "", "", ""))

	def post(self):
		m = self.request.get("month")
		d = self.request.get("day")		
		y = self.request.get("year")
		t = self.request.get("time")
		if m == "" or d == "" or y == "" or t == "":
			self.response.out.write(RenderAddDatePage(m, d, y, t, "Fill in all the fields"))
		else:
			gameDate = GameDate(date=datetime.datetime(month=int(m), day=int(d), year=int(y)), time=t)
			gameDate.put()
			memcache.delete("gamedates")
			values = { "message":"Date added!"}
			path = os.path.join(os.path.dirname(__file__), 'templates/add_gamedate.html')
			self.response.out.write(template.render(path, values))
	
class GamesHandler(webapp2.RequestHandler):
	def get(self):
		current_games = updateCurrentGames()
		memcache.set('gamedates', current_games)
		for game in current_games:
			if game.isThisWeek():
				logging.info("GAME THIS WEEK")
		values = { "games" : current_games}
		path = os.path.join(os.path.dirname(__file__), 'templates/games.html')
		self.response.out.write(template.render(path, values))
		
"""
player type

regular
sub
out-of-towner
goalie


send emails to players who are 'regulars' that have not committed or specified out
"""

app = webapp2.WSGIApplication([
    ('/', MainHandler),
	('/schedule', ScheduleHandler),
	('/player/(.*)', PlayerHandler),
	('/players', PlayersHandler),
	('/subs', SubsHandler),
	('/rosters', RosterHandler),
	('/signup', SignupHandler),
	('/edit', PlayerEditHandler),
	('/games', GamesHandler),
	('/addGameDate', AddGameDateHandler),
	('/addComment', AddCommentHandler)
], debug=True)
