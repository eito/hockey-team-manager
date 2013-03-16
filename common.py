#!/usr/bin/env python

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
from models.GameDate import localTime
from models import Comment

from pst import Pacific_tzinfo

def GetEmailListAllIn():
	to_list = []
	for player in GetAllPlayers():
		if player.inThisWeek:
			if player.email and player.email != "":
				to_list.append(player.email)
	return to_list
	
def GetEmailList(regulars=False, subs=False):
	to_list = []
	for player in GetAllPlayers():
		if player.email and player.email != "":
			if regulars and subs:
				to_list.append(player.email)
			elif regulars and not player.sub:
				to_list.append(player.email)
			elif subs and player.sub:
				to_list.append(player.email)
	return to_list

def GetNextGame():
	games = GetAllGames()
	if games:
		return games[0]
	else: 
		return None
	
def GetAllGames():
	games = memcache.get('gamedates')
	if not games:
		games = GameDate.all()
		games.order('date')
	return games

def GetAllPlayers():
	players = memcache.get('players')
	if not players:
		players = Player.all()
		players.order("lname")
		players.order("fname")			
		memcache.set('players', players)
	return players

def GetAllSubs():
	players = GetAllPlayers()
	subs = []
	for player in players:
		if player.sub:
			subs.append(player)
	return subs
	
def updateCurrentGames():
	games = memcache.get('gamedates')
	if not games:
		games = GameDate.all()
		games.order('date')			
	current_games = []
	deletedGame = False
	now = localTime()
	datetimenow = datetime.datetime(month=now.month, year=now.year, day=now.day)	
	for game in games:
		#if game.date.month <= now.month and game.date.day < now.day and game.date.year <= now.year:
		if game.date < datetimenow:
			game.delete()
			deletedGame = True
		else:
			current_games.append(game)
	# when we delete a game, we should also
	# reset all players to be OUT and NOT goalie
	if deletedGame:
		players = Player.all()
		for player in players:
			player.inThisWeek = False
			if not player.sub:
				player.goalie = False
			player.team = ""
			player.put()
		memcache.set('players', players)
		comments = Comment.all()
		for comment in comments:
			comment.delete()
	return current_games
