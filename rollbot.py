#!/usr/bin/python
# -*- coding: latin-1 -*-
#import os, sys

# Import what's needed.

import socket, string, os, time
import json
import urllib2
import random
import urlparse
from datetime import datetime


#define ircsock
ircsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# IRC variables
server = 'irc.freenode.net'
port = 6667
channel = ['#tagprobots', '#tagpro2', '#tagpromods', '#tagpro', '#TPMods']
botnick = "rollbot2"
password = ''
prefix = '|'

# Majestic owner
owner = ['turtlemansam']
owner_pass = ''

# Connecting to IRC and shit
def ping(content):
	global last_ping
	ircsock.send("PONG :" + content + "\n")
	last_ping = time.time()
def sendmsg(chan , msg):
	ircsock.send(("PRIVMSG " + chan + " :" + msg + "\n").encode("utf-8"))
def joinchan(chan):
	ircsock.send("JOIN " + chan + "\n")
def leavechan(chan):
	ircsock.send("PART " + chan + "\n")

def connect():
	print "connecting...\n"
	ircsock.connect((server, port))
	ircsock.send("PASS " + password + "\n")
	ircsock.send("USER "+ botnick +" "+ botnick +" "+ botnick +" :rollbot\n")
	ircsock.send("NICK " + botnick + "\n")
	registered = 0
	while not registered:
		ircmsg = ircsock.recv(2048)
		connect_msgs = ircmsg.split("\n")
		for x in connect_msgs:
			print x
			if x[0:4] == "PING":
				ping(x[6:])
			if x.count(" 001 ") > 0:
				registered = 1

	for i in range(0,len(channel)):
		joinchan(channel[i])

# For TwitchBot

# List of currently live channels, defaults empty (duh), plus another list of the game they are playing
online = []
games = []

def checkStreams():
	print 'Entering checkStreams'
	global last_update
	global online
	global games
	# Initial new lists of online channels + games, this will replace the existing one when we're done
	online_new = []
	games_new = []
	# Initial API links
	urlt = 'https://api.twitch.tv/kraken/streams?channel='
	last_update = time.time()
	# read streams file
	stramlist = open('stramlist.txt','r')
	print 'entering loop'
	while 1:
		# Read a line of the stream list, removing the newline at the end
		read_stream = stramlist.readline()[:-1]
		# if end of list, we're done, now put that API link to use
		if read_stream == '':
			print 'Done reading'
			stramlist.close()
			try:
				print 'Checking Twitch'
				datat = json.load(urllib2.urlopen(urlt))
			except:
				print 'Something went wrong checking Twitch'
				return
			for i in range(0,len(datat["streams"])):
				# Set some default values for these variables
				# Partly just in case, partly because I don't know python
				display_name = "SomethingBroke"
				stream_title = "Something broke"
				game_playing = "Something broke"
				site = "Twitch"
				# Streams only show up if online, so get info
				display_name = datat["streams"][i]["channel"]["display_name"]
				stream_title = datat["streams"][i]["channel"]["status"]
				game_playing = datat["streams"][i]["game"]
				list_name = display_name + " (" + "http://twitch.tv/" + display_name + ")"
				link = "http://twitch.tv/" + display_name
				online_new.append(list_name)
				games_new.append(game_playing)
				# if stream is in the CURRENT online list playing the same game, nothing to announce
				# if stream is in the CURRENT online list and their game doesn't match, announce new game
				if list_name in online and games[online.index(list_name)] != game_playing:
					announceStream(None,list_name,stream_title,game_playing,site,link,0,1)
				# if stream is NOT in the CURRENT online list, they just went live, announce
				elif list_name not in online:
					announceStream(None,display_name,stream_title,game_playing,site,link,0,0)
			# replace the online/game list with the ones we just made
			print 'list swap time\nonline: ' + str(len(online)) + '\nonlinenew: ' + str(len(online_new)) + '\n'
			online = online_new
			games = games_new
			return
		# back to reading the file, check which site t/h the channel is and get name
		site = read_stream.split(' ')[0]
		name = read_stream.split(' ')[1]
		# append the channel name to the appropriate API link
		if site == 't':
			urlt = urlt + name + ","
			
def announceStream(chan,name,title,game,site,link,viewers,form):
	# form 0 = Just went live, 1 = changed games, 2 = random stream
	# Freaky unicode characters will break things, so don't display the title in that case
	if not title:
		title = "Untitled Broadcast"
	if not game:
		game = "nothing"
	try:
		title = "\"" + title + "\""
	except:
		title = "(error in title)"
	title = title.replace('\n','')
	title = title.replace('\r','')
	if form == 0:
		for i in range(0, len(channel)):
			sendmsg(channel[i],name + " just went live on " + site + " playing " + game + " - " + title + " - " + link)
	if form == 1:
		for k in range(0, len(channel)):
			sendmsg(channel[k],name + " switched games to " + game + " - " + title + " - " + link)
	if form == 2:
		sendmsg(chan,name + " playing " + game + " for " + str(viewers) + " viewers - " + title + " - " + link)


# Main Commands

def commands(nick, chan, msg):
	# handling pivate messages
	if msg.split(" ")[2] == botnick:
		chan = nick

	# define command
	command = msg.split(" ")[3]

	# get argument, only if it exists
	if len(msg.split(" ")) == 4:
		argument = None
	else:
		argument = msg.split(" ")[4]

	# Command: About
	if (command == ":" + prefix + "about"):
		sendmsg(chan, "Hi my name is rollbot and currently turtlemansam is holding me hostage. If anyone could 934-992-8144 and tell me a joke to help pass the time, that would be great.")
	# Command: commands
	elif (command == ":" + prefix + "commands"):
		sendmsg(chan, "About, flirt, fortune, insult, ISITALLCAPSHOUR, mods, netsplit, rate, streams, tagpro, weather")
	# Command: owner commands
	elif (command == ":" + prefix + "owner"):
		sendmsg(chan, "join, part, quit")
	# Command: Help
	elif (command == ":" + prefix + "help"):
		if argument == None:
			sendmsg(chan, "Which command would you like help with?")
		elif argument == "mods":
			sendmsg(chan, "|mods - Notifies in-game moderators")
		elif argument == "netsplit":
			sendmsg(chan, "|netsplit - technically...")
		elif argument == "weather":
			sendmsg(chan, "|weather - Accurently predicts the weather in your area")
		elif argument == "insult":
			sendmsg(chan, "|insult - Send a mean insult to any user. Takes 1 argument")
		elif argument == "tagpro":
			sendmsg(chan, "|tagpro - Have me respond with what kind of game I wish TagPro was")
		elif argument == "flirt":
			sendmsg(chan, "|flirt - Sends a cheesy flirt message to the channel")
		elif argument == "fortune":
			sendmsg(chan, "|fortune - Have me accurently predict your fortune")
		elif argument == "ISITALLCAPSHOUR":
			sendmsg(chan, "|ISITALLCAPSHOUR - Checks if it's all caps hour (1 o'clock EST)")
		elif argument == "rate":
			sendmsg(chan, "|rate - Rate any user based on their nick. Takes 1 argument")
		elif argument == "streams":
			sendmsg(chan, "|streams - Checks if any approved streamers are currently online")
		elif argument == "commands":
			sendmsg(chan, "|commands - Recieve a list of all commands")
		elif argument == "about":
			sendmsg(chan, "|about - Learn about me and my owner!")
		elif argument == "help":
			sendmsg(chan, "|help - Recieve more info about any command")
		else:
			sendmsg(chan, "Sorry! That's not a command you dumb fuck")

	# Trigger: hey
	elif ircmsg.find(":" + "hey " + botnick or ":" + "hello " + botnick or ":" + "hi " + botnick) != -1:
		sendmsg(chan, "Hey " + nick + "!")
	# Trigger: hi
	elif ircmsg.find(":" + "hi " + botnick) != -1:
		sendmsg(chan, "Hey " + nick + "!")
	# Command: mods
	elif (command == ":" + "!mods"):
		if chan == nick:
			sendmsg(nick, "Sorry! You must be in a channel to use this command")
		elif chan == "#TPmods":
			ircsock.send("NOTICE " + nick + " :" + nick + ": The mods have recieved your request. Please be patient\n")
			sendmsg("#tagpromods", "Mod request from " + nick + " in " + chan + "!")
			sendmsg("#tagpromods", "Mods: Flail, Hoog, Watball, Corhal, Ly, tim-sanchez, _Ron, Aaron215, JGibbs, Radian, cz, TinkerC, Bull_tagpro, pooppants, turtlemansam, McBride36, deeznutz, bizkut, poopv, Rems, Rambo, bbq, Akiki, TimeMod, rDuude, yo_cat, Virtulis")
		else:
			ircsock.send("NOTICE " + nick + " :" + nick + ": The mods have recieved your request. Please type /join #TPmods and be patient.\n")
			sendmsg("#tagpromods", "Mod request from " + nick + " in " + chan + "!")
			sendmsg("#tagpromods", "Mods: Flail, Hoog, Watball, Corhal, Ly, tim-sanchez, _Ron, Aaron215, JGibbs, Radian, cz, TinkerC, Bull_tagpro, pooppants, turtlemansam, McBride36, deeznutz, bizkut, poopv, Rems, Rambo, bbq, Akiki, TimeMod, rDuude, yo_cat, Virtulis")


	# Command: netsplit
	elif (command == ":" + prefix + "netsplit"):
		sendmsg(chan, "technically we all netsplit http://pastebin.com/mPanErhR")
	# Command: weather
	elif (command == ":" + prefix + "weather"):
		sendmsg(chan, "look out your goddamn window")
	# Trigger: ,
	#elif ircmsg.find(" ,") != -1:
	#	sendmsg(chan, "nice floating comma dickbrain")
	# Trigger: can
	elif ircmsg.find(":" + botnick + " can ") != -1:
		sendmsg(chan, "hey " + nick + " how bout you dont tell me what to do")
	# Trigger: lol
	elif ircmsg.find(":lol " + botnick) != -1:
		sendmsg(chan, "stop laughing at me im not a fucking peanut")
	# Trigger: wat
	#elif (command == ":" + "wat"):
	#	sendmsg(chan, "no u")
	# Command: Insult
	elif (command == ":" + prefix + "insult"):
		if argument == None:
			sendmsg(chan, "Who shall I insult?")
		else:
			sendmsg(chan, "Your a pretty cool guy, " + argument + "!")
			sendmsg(chan, (random.choice(list(open('insults.txt')))))
	# Command: TagPro
	elif (command == ":" + prefix + "tagpro"):
		sendmsg(chan, "I wish tagpro was " + (random.choice(list(open('iWishTagProWas.txt')))))
	# Command: Flirt
	elif (command == ":" + prefix + "flirt"):
		sendmsg(chan, (random.choice(list(open('flirt.txt')))))
	# Command: fortune
	elif (command == ":" + prefix + "fortune"):
		sendmsg(chan, nick + ", " + (random.choice(list(open('fortune.txt')))))
	# Command: ISITALLCAPSHOUR
	elif (command == ":" + prefix + "ISITALLCAPSHOUR"):
		now = datetime.now()
		if now.hour == 13:
			sendmsg(chan, "YES IT IS, BITCHES")
		else:
			sendmsg(chan, "no " + nick + ", it is not.")
	# Command: rate
	elif (command == ":" + prefix + "rate"):
		if argument == None:
			sendmsg(chan, "Who do you want me to rate?")
		else:
			sendmsg(chan, argument + " has a rating of: %s" % (random.randint(1, 100)))
	# Command: streams
	#elif (command == ":" + prefix + "streams"):
	#	checkStreams()
	#	if not online:
	#		sendmsg(chan, "No TagPro streams online.")
	#	else:
	#		sendmsg(chan, "Currently live: " + ', '.join(online))
	# Trigger: slap
	elif ircmsg.find("slaps " + botnick) != -1:
		sendmsg(chan, "bitch ill slap you right back")
	# Command: roll
	elif (command == ":" + prefix + "roll"):
		sendmsg(chan, "Sorry %s, I can't do that right now." % (nick))
	# Command: !ticket
	elif (command == ":!ticket"):
		sendmsg(chan, "http://support.koalabeast.com/#/appeal")

	# Owner commands
	if nick in owner:
		# quit
		if (command == ":" + prefix + "quit"):
			ircsock.send("QUIT :rollbot's out!\n")
			ircsock.shutdown(1)
			ircsock.close()
			exit()
		# join
		elif (command == ":" + prefix + "join" and argument != None):
			joinchan(argument)
			channel.append(argument)
		# part
		elif (command == ":" + prefix + "part"):
			leavechan(chan)

# lets connect
connect()

while 1:
	try:
		now = time.time()
		ircmsg = ircsock.recv(2048) # get data
		ircmsg = ircmsg.strip('\n\r') # remove new lines
		print(ircmsg)

		if ircmsg.find("PING :") > -1:
			ping(ircmsg[6:])

		if ircmsg.find(' PRIVMSG ') != -1:
			nick = ircmsg.split('!')[0][1:]
			comchan = ircmsg.split(' PRIVMSG ')[-1].split(' :')[0]
			commands(nick,comchan,ircmsg)
	except socket.timeout:
		print 'Disconnected'
		ircsock.close()
		ircsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		connect()