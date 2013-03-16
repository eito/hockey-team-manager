import webapp2
import os
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.api import memcache
from google.appengine.api import mail

import logging
import json
import models
import datetime
from models import Player
from models import GameDate
from common import *

"""
self.response.headers['Content-Type'] = 'application/json'
if self.request.get('f') == 'pretty':
	self.response.out.write(json.dumps(jsonResponse, indent=2))
else:
	self.response.out.write(json.dumps(jsonResponse))
"""

class BaseJSONHandler(webapp2.RequestHandler):
	def get(self, jsonResponse={}):
		self.response.headers['Content-Type'] = 'application/json'
		if self.request.get('f') == 'pretty':
			self.response.out.write(json.dumps(jsonResponse, indent=2))
		else:
			self.response.out.write(json.dumps(jsonResponse))
			
class PlayersJSONHandler(BaseJSONHandler):
	def get(self):
		players = GetAllPlayers()
		jsonResponse = {}
		jsonResponse['players'] = []
		for player in players:
			playerJson = player.toJson()
			jsonResponse['players'].append(playerJson)
		return super(PlayersJSONHandler, self).get(jsonResponse)

class SubsJSONHandler(BaseJSONHandler):
	def get(self):
		subs = GetAllSubs()
		jsonResponse = {}
		jsonResponse['subs'] = []
		for sub in subs:
			subJson = sub.toJson()
			jsonResponse['subs'].append(subJson)
		return super(SubsJSONHandler, self).get(jsonResponse)

class GamesJSONHandler(BaseJSONHandler):
	def get(self):
		games = GetAllGames()
		jsonResponse = {}
		jsonResponse['games'] = []
		for game in games:
			gameJson = game.toJson()
			jsonResponse['games'].append(gameJson)
		return super(GamesJSONHandler, self).get(jsonResponse)

class RostersJSONHandler(BaseJSONHandler):
	def get(self):
		players = GetAllPlayers()
		jsonResponse = {}
		jsonResponse['rosters'] = {}
		jsonResponse['rosters']['white'] = {}
		jsonResponse['rosters']['blue'] = {}
		blueGoalieJson = {}
		bluePlayersJson = []
		whiteGoalieJson = {}
		whitePlayersJson = []
		for player in players:
			if player.inThisWeek:
				if player.team == 'white':
					if player.goalie:
						whiteGoalieJson = player.toJson()
					else:
						whitePlayersJson.append(player.toJson())
				else: #blue
					if player.goalie:
						blueGoalieJson = player.toJson()
					else:
						bluePlayersJson.append(player.toJson())
		jsonResponse['rosters']['white']['goalie'] = whiteGoalieJson
		jsonResponse['rosters']['white']['skaters'] = whitePlayersJson
		jsonResponse['rosters']['blue']['goalie'] = blueGoalieJson
		jsonResponse['rosters']['blue']['skaters'] = bluePlayersJson
		return super(RostersJSONHandler, self).get(jsonResponse)
		
app = webapp2.WSGIApplication([
	('/json/players', PlayersJSONHandler),
	('/json/subs', SubsJSONHandler),
	('/json/games', GamesJSONHandler),
	('/json/rosters', RostersJSONHandler),
], debug=True)