import threading, time, re
import arrow
from willie.tools import stderr
from willie import web
import willie.module
import json

import os, sys
sys.path.append(os.path.dirname(__file__))

from handmade import command, info, whitelisted, adminonly, whitelisted_streamtime, adminonly_streamtime
from handmade_stream import defaultTz, isCurrentlyStreaming, timer, getStreamAt
from handmade import qaInfo

started = arrow.now(defaultTz)

class FakeTrigger():
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

emptyRE = re.compile("()()")


##NOTE(chronister): Difference between @reminder and @interval is that @reminder spoofs the arguments
#   that are normally passed to module commands (a bot with .say(), and a Trigger)
def reminder(*args, **kwargs):

    def mutate(func):
        def say_wrapper(bot):
            def say(text, max_messages=1):
                for channel in bot.channels:
                    bot.msg(channel, text, max_messages)
            return say
        def wrap(bot):
            bot.say = say_wrapper(bot)

            trig = FakeTrigger(nick=":", admin=True, group= emptyRE.match("").group)
            func(bot, trig)
        return willie.module.interval(*args)(wrap)
    return mutate

def setup(bot):
    bot.talkative = True

@adminonly_streamtime
@whitelisted
@command("reminders")
def reminderToggle(bot, trigger):
    if (trigger.group(2) and trigger.admin):
        args = trigger.group(2)
        if (args.lower() == "on"):
            reminderOn(bot, trigger)
            return
        if (args.lower() == "off"):
            reminderOff(bot, trigger)
            return
    bot.say("Reminders are currently %s." % ("on" if bot.talkative else "off"))


@adminonly
@command("remindoff", "shutup", "shh", hide=True, hideAlways=True)
def reminderOff(bot, trigger):
    bot.talkative = False
    bot.say("Reminders have been turned off.")

@adminonly
@command("remindon", "speakup", hide=True, hideAlways=True)
def reminderOn(bot, trigger):
    bot.talkative = True
    bot.say("Reminders have been switched on.")

# @willie.module.event('JOIN')
# @willie.module.rule('.*')
# def say_hi(bot, trigger):
#     bot.msg(trigger.sender, 'Hey there!')

@reminder(600)
def remindTimer(bot, trigger):
    if (isCurrentlyStreaming()):
        trigger.nick = "Timing update"
        timer(bot, trigger)

@reminder(300)
def remindQA(bot, trigger):
    trigger.nick = "Reminder"
    now = arrow.now()
    stream = getStreamAt(now)
    if (stream != None and stream.getQaStart() < now and now < stream.getEnd()):
        qaInfo(bot, trigger)

# wasUp = False
# streamURL="https://api.twitch.tv/kraken/streams/handmade_hero"
# @reminder(60) ##TODO(chronister): Is once a minute too often?
# def checkStreamStatus(bot, trigger):
#     try:
#         response = web.get(streamURL)
#     except Exception as e:
#         stderr("Couldn't access twitch API! %s" % e.message)
#         return

#     if response:
#         trigger.nick = "Stream Notice"

#         result = json.loads(response)
#         try:
#             up = result["stream"] != "null"
#             if (up and not(wasUp)):
#                 bot.say("Handmade Hero just went live!")
#             elif (not(up) and (wasUp)):
#                 bot.say("Handmade hero is no longer live.")

#             wasUp = up
#             return
#         except Exception as e:
#             stderr("Unexpected response from twitch API: %s" % str(result))
#     else:
#         stderr("No response from twitch API")