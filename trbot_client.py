#!/usr/bin/python3
# -*- coding: utf-8 -*-
import re
import random
import datetime
import asyncio
import os
import discord
import shlex
import sys
from trbot import *

QUOTE_LOCK = asyncio.Lock()

# Load the unique Discord API token
#with open('discord_api_token.txt', "r") as f:

TOKEN = str(sys.argv[1])
CLIENT = discord.Client()
REMINDER_DICT = dict()
TOTAL_REMINDERS = 0

@CLIENT.event
async def on_message_edit(before, after):
    if before.author == CLIENT.user:
        return
    # If an user edit a command message after the bot has already responded, add :eyes: reaction (I see what you did)
    if before.content.startswith('!roll ') or before.content == '!roll' or before.content.startswith('!rand ') or before.content == '!rand' or before.content.startswith('!8ball ') or before.content.startswith('!eightball ') or before.content == '!8ball' or before.content == '!eightball':
        await after.add_reaction("👀")

@CLIENT.event
async def on_message(message):
    global CURRENT_QUOTE
    global TOTAL_REMINDERS
    global REMINDER_DICT
    reminder = None
    try:
        # We do not want the bot to reply to itself
        if message.author == CLIENT.user:
            if re.search(r"rolled \*\*100\*\*", message.content):
                await message.add_reaction("💯")
                return

        msg = ""

        # Commands - !help, !roll, !rand, !8ball, !quote
        if message.content == '!help' or (re.search("help", message.content, re.IGNORECASE) and CLIENT.user in message.mentions):
            print('User %s (ID: %s, Guild: %s) made a command %s' % (message.author.name, message.author.id, message.guild, message.content))
            msg = 'List of commands:\n**!roll** - gives random dice rolls and calculates the resulting mathematical expression. Example: `!roll (1d100+10)/10`\n**!roll-repeat** - first argument is a dice roll/anything that would work with !roll, second argument is how many times it should be repeated. Example: `!roll-repeat 2d20+2, 4`\nUse `d` for regular dice and `t` for Traveller dice. Does not apply to commands below.\n\n**!roll-sr** rolls Shadowrun dice in format: `number of dice`d`limit`l `>` `threshold`. No math operations are supported. Example: `!roll-sr 5d5l > 3`\n**!roll-asoiaf** rolls ASOIAF dice in format: `number of dice`d`bonus`b. No math operations are supported. Example: `!roll-asoiaf 5d1b`\n**!rand** - returns a random number from given range (inclusive). Example: `!rand 1,10`\n**!8ball**, **!eightball** - gives a random eightball answer.\n**!quote** - gives Thought of the Day.\n**!fortune**, **!literature**, **!riddle** - works like UNIX `fortunes` command, with dicts being separate.\n**!remindMe** - will send you a DM with the contents of your reminder. Format: `message, #hours/minutes/seconds`. Can do various time units at the same time. MESSAGE CANNOT CONTAIN COMMAS'
        elif message.content.startswith('!roll ') or message.content == '!roll':
            print('User %s (ID: %s, Guild: %s) made a command %s' % (message.author.name, message.author.id, message.guild, message.content))
            if message.content.strip() == '!roll':
                msg = '{0.author.mention} specified an invalid dice expression.'
            else:
                msg = await get_roll(message, True)
        elif message.content.startswith('!roll-sr ') or message.content == '!roll-sr':
            print('User %s (ID: %s, Guild: %s) made a command %s' % (message.author.name, message.author.id, message.guild, message.content))
            if message.content.strip() == '!roll-sr':
                msg = '{0.author.mention} specified an invalid Shadowrun dice expression.'
            else:
                msg = await get_shadowrun_roll(message)
        elif message.content.startswith('!roll-asoiaf ') or message.content == '!roll-asoiaf':
            print('User %s (ID: %s, Guild: %s) made a command %s' % (message.author.name, message.author.id, message.guild, message.content))
            if message.content.strip() == '!roll-asoiaf':
                msg = '{0.author.mention} specified an invalid ASOIAF dice expression.'
            else:
                msg = await get_asoiaf_roll(message)
        elif message.content.startswith('!roll-repeat ') or message.content == '!roll-repeat' or message.content.startswith('!roll-r ') or message.content == '!roll-r':
            print('User %s (ID: %s, Guild: %s) made a command %s' % (message.author.name, message.author.id, message.guild, message.content))
            if message.content.strip() == '!roll-repeat' or message.content.strip() == '!roll-r':
                msg = '{0.author.mention} specified an invalid repeated dice expression.'
            else:
                msg = await get_repeated_roll(message, True)
        elif message.content.startswith('!rand ') or message.content == '!rand':
            print('User %s (ID: %s, Guild: %s) made a command %s' % (message.author.name, message.author.id, message.guild, message.content))
            if message.content.strip() == '!rand':
                msg = '{0.author.mention} specified an invalid rand expression.'
            else:
                msg = await get_rand(message)
        elif message.content.startswith('!8ball ') or message.content.startswith('!eightball ') or message.content == '!8ball' or message.content == '!eightball':
            print('User %s (ID: %s, Guild: %s) made a command %s' % (message.author.name, message.author.id, message.guild, message.content))
            msg = '{0.author.mention}, 🎱 says: **%s**' % await get_eightball()
        elif message.content.startswith('!quoteoftheday ') or message.content.startswith('!quote ') or message.content.startswith('!thought ') or message.content.startswith('!thoughtoftheday ') or message.content == '!quoteoftheday' or message.content == '!quote' or message.content == '!thought' or message.content == '!thoughtoftheday':
            print('User %s (ID: %s, Guild: %s) made a command %s' % (message.author.name, message.author.id, message.guild, message.content))
            # This could be moved to a separate function
            date_now = datetime.datetime.now()
            if date_now.date() > CURRENT_QUOTE[1].date():
                with await QUOTE_LOCK:
                    #Check again after lock was lifted
                    if date_now.date() > CURRENT_QUOTE[1].date():
                        CURRENT_QUOTE = (await get_quote_of_the_day(QUOTES_FILE, QUOTES_LIST), date_now)
            # Easter egg for one guild
            msg = '%sThought of the Day: **%s**' % ("Midwinter's " if int(message.guild.id) == 389536986261618688 else "", CURRENT_QUOTE[0])
        # fortune module
        elif message.content.startswith('!fortune ') or message.content == '!fortune':
            print('User %s (ID: %s, Guild: %s) made a command %s' % (message.author.name, message.author.id, message.guild, message.content))
            msg = '{0.author.mention} 🔮 says:\n%s' % await get_fortune(FORTUNES_FILE, FORTUNES_LIST)
        elif message.content.startswith('!literature ') or message.content == '!literature':
            print('User %s (ID: %s, Guild: %s) made a command %s' % (message.author.name, message.author.id, message.guild, message.content))
            msg = '{0.author.mention} 📚:\n%s' % await get_fortune(LITERATURE_FILE, LITERATURE_LIST)
        elif message.content.startswith('!riddle ') or message.content == '!riddle':
            print('User %s (ID: %s, Guild: %s) made a command %s' % (message.author.name, message.author.id, message.guild, message.content))
            msg = '{0.author.mention} 🤔:\n%s' % await get_fortune(RIDDLES_FILE, RIDDLES_LIST)
        elif message.content == '!remindMeQueue' or message.content == '!remindmequeue':
            print('User %s (ID: %s, Guild: %s) made a command %s' % (message.author.name, message.author.id, message.guild, message.content))
            msg = "{0.author.mention}, you have %s reminders in queue!" % ("0" if message.author not in REMINDER_DICT else str(REMINDER_DICT[message.author]))
        elif message.content.startswith('!remindMe ') or message.content == '!remindMe' or message.content.startswith('!remindme ') or message.content == '!remindme':
            print('User %s (ID: %s, Guild: %s) made a command %s' % (message.author.name, message.author.id, message.guild, message.content))
            if message.author in REMINDER_DICT and REMINDER_DICT[message.author] >= 5:
                msg = "{0.author.mention} has too many reminders (5) already in queue!"
            elif TOTAL_REMINDERS >= 100:
                msg = "I already have too many reminders to process, sorry! :("
            else:
                current_time = datetime.datetime.now()
                reminder = await process_reminder_message(message, current_time)
                if(reminder):
                    msg = reminder[0]
                    if message.author in REMINDER_DICT:
                        REMINDER_DICT[message.author] += 1
                        TOTAL_REMINDERS += 1
                    else:
                        REMINDER_DICT[message.author] = 1
                        TOTAL_REMINDERS += 1

        #GOOD BOY MODULE
        else:
            if CLIENT.user in message.mentions:
                if EXPLAIN_BOT_RE.search(message.content):
                    print('User %s (ID: %s, Guild: %s) asked to explain %s' % (message.author.name, message.author.id, message.guild, message.content))
                    await message.channel.send("%s, %s" % (message.author.mention, random.choice(EXPLAIN).format(message)))
                    return
                if BAD_BOT_RE_MENTION.search(message.content):
                    print('User %s (ID: %s, Guild: %s) made a bad bot comment :( %s' % (message.author.name, message.author.id, message.guild, message.content))
                    await message.add_reaction(random.choice(BADBOYREACTIONS))
                    return
                if HIGH_FIVE_RE.search(message.content):
                    print('User %s (ID: %s, Guild: %s) made a high five comment :( %s' % (message.author.name, message.author.id, message.guild, message.content))
                    await message.add_reaction("✋")
                    return
            if HIGH_FIVE_RE.search(message.content):
                async for item in message.channel.history(limit=5, before=message):
                    if item.author == CLIENT.user:
                        print('User %s (ID: %s, Guild: %s) made a high five comment :( %s' % (message.author.name, message.author.id, message.guild, message.content))
                        await message.add_reaction("✋")
                        return
            if BAD_BOT_RE.search(message.content):
                async for item in message.channel.history(limit=5, before=message):
                    if item.author == CLIENT.user:
                        print('User %s (ID: %s, Guild: %s) made a bad bot comment :( %s' % (message.author.name, message.author.id, message.guild, message.content))
                        await message.add_reaction(random.choice(BADBOYREACTIONS))
                        return
            if CLIENT.user in message.mentions and GOOD_BOT_RE_MENTION.search(message.content):
                print('User %s (ID: %s, Guild: %s) made a good bot comment :( %s' % (message.author.name, message.author.id, message.guild, message.content))
                await message.add_reaction(random.choice(GOODBOYREACTIONS))
                return
            if GOOD_BOT_RE.search(message.content):
                async for item in message.channel.history(limit=5, before=message):
                    if item.author == CLIENT.user:
                        print('User %s (ID: %s, Guild: %s) made a good bot comment %s' % (message.author.name, message.author.id, message.guild, message.content))
                        await message.add_reaction(random.choice(GOODBOYREACTIONS))
                        return

        if int(message.author.id) == 238234001708417024:
            if message.content.startswith('!wordcloud '):
                split_message = shlex.split(message.content.replace(", ", ","))
                print(split_message)
                size = int(split_message[1])
                try:
                    channels_parsed = { x.strip() for x in split_message[2].split(",") }
                    channels = [x for x in CLIENT.get_all_channels() if x.name.lower().strip() in channels_parsed]
                except:
                    channels = None
                if not channels:
                    channels = [message.channel]
                return_tuple = await get_text_from_channels(channels, CLIENT, size)
                if not return_tuple:
                    return
                log_file = return_tuple[2]
                image_file = return_tuple[1]
                num_messages =  return_tuple[0]
                temp_msg = "{0.author.mention}, here is a Word Cloud for channels: `%s`\nThere were %s messages." % ('`, `'.join(x.name for x in channels), str(num_messages))
                await message.channel.send(temp_msg.format(message), file=image_file)
                await message.author.send(file=log_file)
                os.remove(log_file)
                os.remove(image_file)
            if message.content.startswith('!wordcloud-user '):
                split_message = shlex.split(message.content.replace(", ", ","))
                print(split_message)
                size = int(split_message[1])
                users = { x.strip() for x in split_message[2].split(",") }
                try:
                    channels_parsed = { x.strip() for x in split_message[3].split(",") }
                    channels = [x for x in CLIENT.get_all_channels() if x.name.lower().strip() in channels_parsed]
                except:
                    channels = None
                if not channels:
                    channels = [message.channel]
                return_tuple = await get_text_from_channels(channels, CLIENT, size, users)
                if not return_tuple:
                    return
                log_file = return_tuple[2]
                image_file = return_tuple[1]
                num_messages =  return_tuple[0]
                temp_msg = "{0.author.mention}, here is a Word Cloud for users `%s` in channels: `%s`\nThere were %s messages." % ('`, `'.join(x for x in users), '`, `'.join(x.name for x in channels), str(num_messages))
                await message.channel.send(temp_msg.format(message), file=image_file)
                await message.author.send(file=log_file)
                os.remove(log_file)
                os.remove(image_file)

        if msg:
            print(msg)
            await message.channel.send(msg.format(message))
        if reminder:
            await message_reminder(current_time, reminder[1], REMINDER_DICT, TOTAL_REMINDERS)
    except:
        # Catch anything
        print(traceback.format_exc())
        await message.channel.send(msg.format("Something went wrong! Please try again."))

@CLIENT.event
async def on_ready():
    # Do all of the below when the bot is started
    global CURRENT_QUOTE
    await get_fortune(FORTUNES_FILE, FORTUNES_LIST)
    await get_fortune(LITERATURE_FILE, LITERATURE_LIST)
    await get_fortune(RIDDLES_FILE, RIDDLES_LIST)
    CURRENT_QUOTE = (await get_quote_of_the_day(QUOTES_FILE, QUOTES_LIST), datetime.datetime.now())
    print('------')
    print('Logged in as')
    print(CLIENT.user.name)
    print(CLIENT.user.id)
    print('------')

CLIENT.run(TOKEN)
