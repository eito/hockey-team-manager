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

# just lists all of the "subs" that are registered
class SubsHandler(webapp2.RequestHandler):
	def get(self):
		subs = GetAllSubs()
		values = {}
		if subs:
			values = {'subs':subs}
		path = os.path.join(os.path.dirname(__file__), 'templates/subs.html')
		self.response.out.write(template.render(path, values))

# main page, shows current week's game and players
# who are in...also shows any notes for that current week
class MainHandler(webapp2.RequestHandler):
    def get(self):
		game = GetNextGame()
		# get all of the players and loop through them to figure out
        # who is "in"
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
        
        # we query all of the comments and order them by time
		comments = Comment.all()
		comments.order("-time")
        
        # the template system takes key/value pairs 
		values = {"game" : game, "inPlayerMap":inPlayerMap, "outPlayers":outPlayers, "comments":comments, "numGoalies": len(inGoalies), "numSkaters":len(inPlayers)}
        
        # this is standard webapp/django template syntax
        # we specify a template to use and a dictionary of values
		path = os.path.join(os.path.dirname(__file__), 'templates/main.html')
		self.response.out.write(template.render(path, values))

# This handles the /rosters endpoint and displays the rosters
# for the current week (empty if they have not been set yet)
class RosterHandler(webapp2.RequestHandler):
    def get(self):
		game = GetNextGame()
		blue = {}
		white = {}
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

# lists all of the registered players
class PlayersHandler(webapp2.RequestHandler):
	def get(self):
		players = GetAllPlayers()
		values = { "players" : players}
		path = os.path.join(os.path.dirname(__file__), 'templates/players.html')
		self.response.out.write(template.render(path, values))

# for given inputs, creates/renders a signup/edit page	
def RenderSignupPage(fname, lname, email, message, phone):
	values = { "fname": fname, "lname": lname, "email":email, "message":message, "phone":phone}
	path = os.path.join(os.path.dirname(__file__), 'templates/signup.html')
	return template.render(path, values)

# handles the signup endpoint for new players
class SignupHandler(webapp2.RequestHandler):
    # for a GET, a user is bringing this page up in the browser
    # show an empty page
	def get(self):
		self.response.out.write(RenderSignupPage("", "", "", "", ""))

    # for a POST, this means the user has clicked "submit" on the page
    # and is either signing up as new, or editing their existing info
	def post(self):
		first_name = self.request.get("fname")
		last_name = self.request.get("lname")		
		email_address = self.request.get("email")
		phone_number = self.request.get("phone")
        # we don't require a phone number, but we don't 
        # want it to be an empty string either
		if phone_number == "":
			phone_number = None
        # make sure they fill out all required fields
		if first_name == "" or last_name == "" or email_address == "":
			self.response.out.write(RenderSignupPage(first_name, last_name, email_address,"Fill in all the fields", phone_number))
		else:
            # if a new player has been created, clear our memcache and add the new player
			memcache.delete('players')
			player = Player(fname=first_name, lname=last_name, email=email_address, goalie=False, rating=0, phone=phone_number)
			player.put()
			values = { "message":"Thank you for signing up!"}
			path = os.path.join(os.path.dirname(__file__), 'templates/success.html')
			self.response.out.write(template.render(path, values))

# This allows an admin to edit ALL players inline
class PlayerEditHandler(webapp2.RequestHandler):
    # the GET happens when the admin browses to an explicit link /edit
	def get(self):
		players = GetAllPlayers()
		values = { "players" : players}
		path = os.path.join(os.path.dirname(__file__), 'templates/edit_players.html')
		self.response.out.write(template.render(path, values))
	
    # the POST happens when the admin submits the form
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

# page for single player
class PlayerHandler(webapp2.RequestHandler):
    # display info for single player
	def get(self, playerId):		
		player = Player.get_by_id(int(playerId))
		if player:
			values = {"player":player}
			path = os.path.join(os.path.dirname(__file__), 'templates/edit_player.html')			
		else:
			values = { "message" : "Error finding player."}
			path = os.path.join(os.path.dirname(__file__), 'templates/success.html')
		self.response.out.write(template.render(path, values))
	
    # single player info has been submitted
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

# called when a comment is posted/added	
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
