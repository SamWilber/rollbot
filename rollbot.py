#!/usr/bin/python
# -*- coding: latin-1 -*-
# import os, sys

# Import what's needed.

import socket
import random
import time
from datetime import datetime
#import praw


#define ircsock
ircsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# IRC variables
server = 'irc.freenode.net'
port = 6667
channel = ["#turtlemansam"]
botnick = "rollbot"
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


def sendmsg(chan, msg):
    ircsock.send(("PRIVMSG " + chan + " :" + msg + "\n").encode("utf-8"))


def joinchan(chan):
    ircsock.send("JOIN " + chan + "\n")


def leavechan(chan):
    ircsock.send("PART " + chan + "\n")

def connect():
    print "connecting...\n"
    ircsock.connect((server, port))
    ircsock.send("PASS " + password + "\n")
    ircsock.send("USER " + botnick + " " + botnick + " " + botnick + " :rollbot\n")
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

    for i in range(0, len(channel)):
        joinchan(channel[i])


# Reddit Topic

#def redditTopic():
#    r = praw.Reddit("IRC Topic Updater - /u/samwilber")
#    subreddit = r.get_subreddit('tagpro')
#    submission = subreddit.get_hot().next()
#    return(submission.title)
#    return(submission.stickied)


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
        sendmsg(chan,
                "Hi my name is rollbot and currently turtlemansam is holding me hostage. If anyone could 934-992-8144 and tell me a joke to help pass the time, that would be great.")
    # Command: commands
    elif (command == ":" + prefix + "commands"):
        sendmsg(chan, "About, flirt, fortune, insult, ISITALLCAPSHOUR, mods, netsplit, rate, tagpro, weather")
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
            sendmsg(chan, "Sorry! That's not a command.")
    # Trigger: hi
    elif ircmsg.find(":" + "hi " + botnick) != -1:
        sendmsg(chan, "Hey " + nick + "!")
    # Command: mods
    elif (command == ":" + "!mods"):
        if chan == nick:
            sendmsg(nick, "Sorry! You must be in a channel to use this command")
        elif chan == "#TPmods":
            ircsock.send("NOTICE " + nick + " :" + nick + ": The mods have received your request. Please be patient\n")
            sendmsg("#tagpromods", "Mod request from " + nick + " in " + chan + ":" + msg.split("!mods")[1])
            sendmsg("#tagpromods",
                    "Mods: Flail, Hoog, Watball, Corhal, Ly, tim-sanchez, _Ron, Aaron215, JGibbs, Radian, cz, TinkerC, Bull_tagpro, pooppants, turtlemansam, McBride36, deeznutz, bizkut, Rems, Rambo, bbq, Akiki, TimeMod, rDuude, yo_cat, Virtulis")
        else:
            ircsock.send(
                "NOTICE " + nick + " :" + nick + ": The mods have received your request. Please type /join #TPmods and be patient.\n")
            sendmsg("#tagpromods", "Mod request from " + nick + " in " + chan + ":" + msg.split("!mods")[1])
            sendmsg("#tagpromods",
                    "Mods: Flail, Hoog, Watball, Corhal, Ly, tim-sanchez, _Ron, Aaron215, JGibbs, Radian, cz, TinkerC, Bull_tagpro, pooppants, turtlemansam, McBride36, deeznutz, bizkut, Rems, Rambo, bbq, Akiki, TimeMod, rDuude, yo_cat, Virtulis")


    # Command: netsplit
    elif (command == ":" + prefix + "netsplit"):
        sendmsg(chan, "technically we all netsplit http://pastebin.com/mPanErhR")
    # Command: weather
    elif (command == ":" + prefix + "weather"):
        sendmsg(chan, "look out your goddamn window")
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
            leavechan(chan)  # lets connect
        # Command: topic
        #elif (command == ":" + prefix + "topic"):
        #    ircsock.send("PRIVMSG Chanserv :topic #tagpro http://tagpro.gg | http://TagPro.reddit.com | {} http://bit.ly/TagProSticky | TagPro Mods have + next to their name. | Mod calls will be redirected to #TPmods\n".format(redditTopic()))

connect()

while 1:
    try:
        now = time.time()
        ircmsg = ircsock.recv(2048)  # get data
        ircmsg = ircmsg.strip('\n\r')  # remove new lines
        print(ircmsg)

        if ircmsg.find("PING :") > -1:
            ping(ircmsg[6:])

        if ircmsg.find(' PRIVMSG ') != -1:
            nick = ircmsg.split('!')[0][1:]
            comchan = ircmsg.split(' PRIVMSG ')[-1].split(' :')[0]
            commands(nick, comchan, ircmsg)
    except socket.timeout:
        print 'Disconnected'
        ircsock.close()
        ircsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connect()