#!/usr/bin/python
# -*- coding: latin-1 -*-
# import os, sys

# Import what's needed.
from datetime import datetime
import random

import socket, string, os, time
import json
import re
from logbook import Logger
import inspect
import sys
import praw

def command(method):  # A decorator to automatically register and add commands to the bot.
    method.is_command = True
    return method

def owner_command(method):
    method.is_command = True
    def wrapper(self, hostmask, source, *args):
        if self.owner.lower() != source.lower():
            return "You can't control me {}!".format(source)
        return method(self, hostmask, source, *args)
    wrapper.is_command = True
    return wrapper


class RollBot:
    CONFIG_LOCATION = "./config.json"

    def __init__(self):
        self.command_list = {}
        self.logger = Logger('RollBot', level=2)
        self.logger.info("RollBot started.")
        self.last_ping = None
        self.registered = False

        with open(self.CONFIG_LOCATION) as f:
            self.config = json.load(f)
        self.nick = self.config['botnick']
        self.owner = self.config['owner']['nick']
        self.channels = set([x.lower() for x in self.config['channel']])
        self.command_prefix = self.config['prefix']

        for name, method in inspect.getmembers(self.__class__, predicate=inspect.ismethod):
            if getattr(method, "is_command", False):
                self.command_list[name] = getattr(self, name)
                self.logger.info("Added '{}' as a command.", name)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


    def send_message(self, channel, message):
        message_template = "PRIVMSG {} :{}"
        self.send_raw(message_template.format(channel, message))

    def send_ping(self, ping_message):
        message_template = "PONG : {}"
        self.send_raw(message_template.format(ping_message))
        self.update_ping_time()

    def join_channel(self, channel):
        if channel:
            message_template = "JOIN {}"
        self.send_raw(message_template.format(channel))

    def leave_channel(self, channel):
        if channel in self.channels:
            message_template = "PART {}"
            self.send_raw(message_template.format(channel))
            self.channels.remove(channel)

    def connect(self):
        server_information = (self.config['server'], self.config['port'])
        self.socket.connect(server_information)
        self.send_raw("PASS " + self.config['password'])
        self.send_raw("USER {} {} {} :{}".format(self.nick, self.nick, self.nick, "rollbot"))
        self.send_raw("NICK " + self.nick)
        self.run_loop()

    @property
    def get_message_from_server(self):
        message = ""
        current_character = self.socket.recv(1)
        while current_character != "\n":
            message += current_character
            current_character = self.socket.recv(1)
        return message

    def run_loop(self):
        message_regex = r"^(?:[:](?P<prefix>\S+) )" \
                        r"?(?P<type>\S+)" \
                        r"(?: (?!:)(?P<destination>.+?))" \
                        r"?(?: [:](?P<message>.+))?$"  # Extracts all appropriate groups from a raw IRC message
        compiled_message = re.compile(message_regex)

        while True:
            try:
                message = self.get_message_from_server
                self.logger.debug("Received server message: {}", message)
                parsed_message = compiled_message.finditer(message)
                message_dict = [m.groupdict() for m in parsed_message][0]  # Extract all the named groups into a dict
                source_nick = ""
                hostmask = ""
                ircmsg = message.strip('\n\r')  # remove new lines
                print(ircmsg)

                if message_dict['prefix'] is not None:
                    if "!" in message_dict['prefix']:  # Is the prefix from a nickname?
                        hostmask = message_dict['prefix'].split("@")[1]
                        source_nick = message_dict['prefix'].split("!")[0]

                if message_dict['type'] == "PING":
                    self.send_ping(message_dict['message'])

                if message_dict['type'] == "PRIVMSG":
                    self.handle_message(hostmask, source_nick, message_dict['destination'], message_dict['message'])

                if message_dict['type'] == "001":  # Registration confirmation message
                    self.registered = True
                    self.logger.info("{} connected to server successfully.", self.nick)
                    for channel in self.config['channel']:
                        self.logger.info("Attempting to join {}", channel)
                        self.join_channel(channel)

            except socket.timeout:
                self.logger.error("Disconnected. Attempting to reconnect.")
                self.socket.close()
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.connect()

    def handle_message(self, hostmask, source, destination, message):
        is_command = message.startswith(self.config['prefix'].encode("utf-8"))
        if is_command:
            self.handle_command(hostmask, source, destination, message)

    def handle_command(self, hostmask, source, destination, message):
        try:
            split_message = message[1:].split()
            command_key = split_message[0].lower()
        except IndexError:
            self.logger.info("No Command")
            return
        arguments = split_message[1:]
        reply_to = destination
        if destination == self.nick:
            reply_to = source  # If it's a private message, reply to the source. Otherwise it's a channel message and reply there.
        if command_key in self.command_list:
            self.logger.info("Received command '{}' from {}", command_key, source)
            return_message = self.command_list[command_key](hostmask, source, reply_to, *arguments)
            if return_message is not None:
                if isinstance(return_message, basestring):  # Is it a string?
                    self.send_message(reply_to, return_message)  # If so, just send it along.
                else:  # Otherwise it's a list or a tuple
                    for message in return_message:  # So let's loop over them all
                        self.send_message(reply_to, message)  # And send them.
        else:
            pass
            #combined_command = self.command_prefix + command_key
            #self.send_message(reply_to, "Sorry, {} isn't a recognized command.".format(combined_command))

    def send_raw(self, message):
        return self.socket.send((message + "\n").encode("utf-8"))

    def update_ping_time(self):
        self.last_ping = time.time()

    def reddit_topic(self):
        r = praw.Reddit("IRC Topic Updater - /u/samwilber")
        subreddit = r.get_subreddit('tagpro')
        submission = subreddit.get_hot().next()
        return "{} {}".format(submission.title, submission.short_link)
        #return(submission.stickied)

    # Commands

    @command
    def about(self, hostmask, source, reply_to, *args):
        return "Hi my name is {} v4.2 and currently turtlemansam is holding me hostage. " \
               "If anyone could 934-992-8144 and tell me a joke to help pass the time, " \
               "that would be great.".format(self.nick)

    @command
    def commands(self, hostmask, source, reply_to, *args):
        return "Available commands: {}".format(", ".join(sorted(self.command_list.keys())))

    @command
    def help(self, hostmask, source, reply_to, helpp=None, *args):
        if helpp is None:
            return "Which command would you like help with?"
        elif helpp == "about":
            return "|about - Learn about me and my owner!"
        elif helpp == "commands":
            return "|commands - Receive a list of all commands"
        elif helpp == "flirt":
            return "|flirt - Sends a cheesy flirt message to the channel"
        elif helpp == "fortune":
            return "|fortune - Have me accurately predict your fortune"
        elif helpp == "help":
            return "|help <command> - Receive more info about any command"
        elif helpp == "insult":
            return "|insult <user> - Send a mean insult to any user"
        elif helpp == "ISITALLCAPSHOUR":
            return "|ISITALLCAPSHOUR - Checks if it's all caps hour (time is unknown)"
        elif helpp == "ip":
            return "!ip - Converts IP's to dots instead of dashes"
        elif helpp == "join":
            return "|join <channel> - Makes the bot join any channel (Owner Command)"
        elif helpp == "mods":
            return "!mods <optional argument> - Notifies in-game moderators of your request. Must be done in #TPMods"
        elif helpp == "netsplit":
            return "|netsplit - technically..."
        elif helpp == "optin":
            return "!optin - Opt yourself into receiving mod calls (Moderator Command)"
        elif helpp == "optout":
            return "!optout - Opt yourself out of receiving mod calls (Moderator Command)"
        elif helpp == "part":
            return "|part <channel> - Makes the bot leave any channel (Owner Command)"
        elif helpp == "ping":
            return "|ping - Returns your exact pong"
        elif helpp == "quit":
            return "|quit - Makes the bot disconnect from IRC (Owner Command)"
        elif helpp == "rate":
            return "|rate <user> - Rate any user based on their nick"
        elif helpp == "roll":
            return "|roll - Something that I will always be able to do"
        elif helpp == "say":
            return "!say <channel> <message> - Have me say anything you want to any channel (Owner Command)"
        elif helpp == "tagpro":
            return "|tagpro - Have me respond with what kind of game I wish TagPro was"
        elif helpp == "ticket":
            return "!ticket - Sends a link to TagPro's support site"
        elif helpp == "topic":
            return "!topic - Updates #tagpro's topic!"
        elif helpp == "warn":
            return "!warn - Warn users in #TPmods to redirect their conversation elsewhere (Moderator Command)"
        elif helpp == "weather":
            return "|weather - Accurately predicts the weather in your area"
        else:
            return "Sorry! I don't recognize that command."
    '''
    @command
    def netsplit(self, source, reply_to, *args):
        return "technically we all netsplit http://pastebin.com/mPanErhR"

    @command
    def weather(self, source, reply_to, *args):
        return "look out your goddamn window"

    @command
    def insult(self, source, reply_to, insultee=None, *args):
        if insultee is None:
            return "Who shall I insult?"
        else:
            with open("insults.txt") as f:
                insult = random.choice(list(f))
            messages = ("You're a pretty cool guy, {}".format(insultee),
                        insult)
            return messages

    @command
    def tagpro(self, source, reply_to, *args):
        random_idea = "I wish tagpro was {}"
        with open("iWishTagProWas.txt") as f:
            return random_idea.format(random.choice(list(f)))

    @command
    def flirt(self, source, reply_to, *args):
        with open('flirt.txt') as f:
            return random.choice(list(f))

    @command
    def fortune(self, source, reply_to, *args):
        with open("fortune.txt") as f:
            return "{}, {}".format(source, random.choice(list(f)))

    @command
    def isitallcapshour(self, source, reply_to, *args):
        now = datetime.now()
        if now.hour == 13:
            return "YES IT IS, BITCHES"
        else:
            return "no, {}, it is not".format(source)

    @command
    def rate(self, source, reply_to, ratee=None, *args):
        if ratee is None:
            return "Who do you want me to rate?"
        else:
            return "{} has a rating of: {}".format(ratee, random.randint(1, 100))

    @command
    def roll(self, source, reply_to, *args):
        return "Sorry {}, I can't do that right now.".format(source)
    '''''

    @command
    def ping(self, hostmask, source, reply_to, *args):
        with open("raccoons.txt") as f:
            return "10{}14, your pong is10 {}14 {}.".format(source, random.randint(0, 100), random.choice(list(f)))

    @command
    def mods(self, hostmask, source, reply_to, *args):
        if reply_to != "#TPmods":
            if source == "WOLOWOLO" or source == "justanotheruser" or source == "MRCOW" or source == "LEBRONxJAMES" or source == "defense_bot":
                return "can you not"
            else:
                return "Sorry! You must use this command in the channel #TPmods | Double click the channel to join."
        else:
            self.send_raw("NAMES #TPmods")
            message = self.get_message_from_server
            ircmsg = message.strip('\n\r')
            try:
                ipp = " (http://tagpro-origin.koalabeast.com/moderate/ips/{})".format(re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', hostmask)[0])
            except IndexError:
                ipp = ""
            if ircmsg.find(' 353 {} '.format(self.nick)) != -1:
                namelist = ircmsg.split(":")[2]
                modlist = " ".join(x[1:] for x in namelist.split() if x.startswith('+'))
                oplist = " ".join(x[1:] for x in namelist.split() if x.startswith('@'))
                modmsg = "- " + ' '.join(args)
                if ' '.join(args) == "":
                    modmsg = ""
                if modlist == "" and oplist == "":
                    self.send_raw("PRIVMSG #TPmods :Sorry {}, all mods are currently AFK. You can stick around or leave your request for one to find later.".format(source))
                else:
                    self.send_raw("PRIVMSG #TagProMods :Mods - {} {}".format(modlist, oplist))
                    self.send_raw("PRIVMSG #TPmods :{} - the mods have received your request. Please stay patient while waiting. Make sure to state the user/issue to speed up the request process.".format(source))
                    self.send_raw("PRIVMSG #TagProMods :Mod request from {}{} in {} {}".format(source, ipp, reply_to, modmsg))

    @command
    def optin(self, hostmask, source, reply_to, *args):
        if reply_to != "#TagProMods":
            return "Sorry! This command is not authorized here."
        else:
            self.send_raw("NAMES #TPmods")
            message = self.get_message_from_server
            ircmsg = message.strip('\n\r')
            if ircmsg.find('+{}'.format(source)) != -1:
                return "You are already on duty, {}.".format(source)
            elif ircmsg.find('{}'.format(source)) != -1:
                self.send_raw("PRIVMSG Chanserv :voice #TPmods {}".format(source))
                return "You are now on duty, {}.".format(source)
            else:
                return "You are not in #TPmods, {}!".format(source)

    @command
    def optout(self, hostmask, source, reply_to, *args):
        if reply_to != "#TagProMods":
            return "Sorry! This command is not authorized here."
        else:
            self.send_raw("NAMES #TPmods")
            message = self.get_message_from_server
            ircmsg = message.strip('\n\r')
            if ircmsg.find('+{}'.format(source)) != -1:
                self.send_raw("PRIVMSG Chanserv :devoice #TPmods {}".format(source))
                return "You are now off duty, {}.".format(source)
            elif ircmsg.find('{}'.format(source)) != -1:
                return "You are already off duty, {}.".format(source)
            else:
                return "You are not in #TPmods, {}!".format(source)

    @command
    def op(self, hostmask, source, reply_to, *args):
        if reply_to != "#TagProMods":
            return "Sorry! This command is not authorized here."
        else:
            self.send_raw("NAMES #TPmods")
            message = self.get_message_from_server
            ircmsg = message.strip('\n\r')
            if ircmsg.find('@{}'.format(source)) != -1:
                return "You are already an operator, {}.".format(source)
            elif ircmsg.find('{}'.format(source)) != -1:
                self.send_raw("PRIVMSG Chanserv :op #TPmods {}".format(source))
                return "You are now an operator, {}.".format(source)
            else:
                return "You are not in #TPmods, {}!".format(source)

    @command
    def deop(self, hostmask, source, reply_to, *args):
        if reply_to != "#TagProMods":
            return "Sorry! This command is not authorized here."
        else:
            self.send_raw("NAMES #TPmods")
            message = self.get_message_from_server
            ircmsg = message.strip('\n\r')
            if ircmsg.find('@{}'.format(source)) != -1:
                self.send_raw("PRIVMSG Chanserv :deop #TPmods {}".format(source))
                return "You are no longer an operator, {}.".format(source)
            elif ircmsg.find('{}'.format(source)) != -1:
                return "You are not an operator, {}.".format(source)
            else:
                return "You are not in #TPmods, {}!".format(source)
    @command
    def ticket(self, hostmask, source, reply_to, tickett=None, *args):
        if tickett is None:
            return "http://support.koalabeast.com/#/appeal"
        else:
            return "http://support.koalabeast.com/#/appeal/{}".format(tickett)

    @command
    def topic(self, hostmask, source, reply_to, *args):
        #self.send_raw("Topic #tagpro")
        #x = self.get_message_from_server
        #message = "".join([a if ord(a) < 128 else '' for a in x])
        #ircmsg = message.strip('\n\r')
        #if ircmsg.find(' 332 {} '.format(self.nick)) != -1:
        #    topic = ircmsg.split("#tagpro :")[1]
        self.send_raw("PRIVMSG ChanServ :TOPIC #tagpro " + u'\u2691' + \
                      " http://tagpro.gg | http://tagpro.reddit.com | {} | " \
                      "TagPro Mods have + next to their name. | " \
                      "Mod calls must be done in #TPmods ".format(self.reddit_topic()) + u'\u2690')

    @command
    def ip(self, hostmask, source, reply_to, *args):
        ipaddress = ' '.join(args)
        if re.match('^[-0-9.]*$', ipaddress):
            return ipaddress.replace("-", ".")
        else:
            return "Sorry, that's not an IP address!"

    @command
    def warn(self, hostmask, source, reply_to, *args):
        if reply_to != "#TagProMods":
            return "Sorry! This command is not authorized here."
        else:
            self.send_raw("NOTICE #TPmods :Please take off-topic discussion to #tagpro")

    @owner_command
    def quit(self, hostmask, source, reply_to, *args):
        self.logger.warn("Shutting down by request of {}", source)
        self.send_raw("QUIT :{}'s out!".format(self.nick))
        self.socket.shutdown(1)
        self.socket.close()
        sys.exit()

    @owner_command
    def join(self, hostmask, source, reply_to, channel=None, *args):
        if channel is None:
            return "Please specify a channel you wish me to join."
        else:
            self.logger.info("Joining {} by request of {}".format(channel, source))
            self.join_channel(channel)

    @owner_command
    def part(self, hostmask, source, reply_to, channel=None, *args):
        if reply_to == source and channel is None:  # If this was a private message, we have no channel to leave.
            return "Sorry, you must run this command in a channel or provide a channel as an argument."
        elif channel is not None:
            if channel in self.channels:
                self.leave_channel(channel)
                return "Left channel {}!".format(channel)
            else:
                return "I don't believe I'm in that channel!"
        else:  # It was a channel message, so let's leave.
            self.leave_channel(reply_to)

    @owner_command
    def say(self, hostmask, source, reply_to, channel=None, *args):
        if reply_to != source:
            return "{} {}".format(channel, ' '.join(args))
        elif channel is not None:
            if channel in self.channels:
                self.send_message(channel, ' '.join(args))
            else:
                return "Whoops! I'm not in the channel {}".format(channel)
        else:
            return "The format is: |say <channel> <message>"

if __name__ == "__main__":
    bot = RollBot()
    bot.connect()