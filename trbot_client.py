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

@CLIENT.event
async def on_message_edit(before, after):
    if before.author == CLIENT.user:
        return
    # If an user edit a command message after the bot has already responded, add :eyes: reaction (I see what you did)
    if before.content.startswith('!roll ') or before.content == '!roll' or before.content.startswith('!rand ') or before.content == '!rand' or before.content.startswith('!8ball ') or before.content.startswith('!eightball ') or before.content == '!8ball' or before.content == '!eightball':
        await CLIENT.add_reaction(after, "👀")

@CLIENT.event
async def on_message(message):
    global CURRENT_QUOTE
    try:
        # We do not want the bot to reply to itself
        if message.author == CLIENT.user:
            if re.search(r"rolled \*\*100\*\*", message.content):
                await CLIENT.add_reaction(message, "💯")
                return

        msg = ""

        # Commands - !help, !roll, !rand, !8ball, !quote
        if message.content == '!help' or (re.search("help", message.content, re.IGNORECASE) and CLIENT.user in message.mentions):
            print('User %s (ID: %s, Server: %s) made a command %s' % (message.author.name, message.author.id, message.server, message.content))
            msg = 'List of commands:\n**!roll** - gives random dice rolls and calculates the resulting mathematical expression. Example: `!roll (1d100+10)/10`\n**!roll-repeat** - first argument is a dice roll/anything that would work with !roll, second argument is how many times it should be repeated. Example: `!roll 2d20+2, 4`\n**!roll-sr** rolls Shadowrun dice in format: `number of dice`d`limit`l `>` `threshold`. No math operations are supported. Example: `!roll-sr 5d5l > 3`\n**!roll-asoiaf** rolls ASOIAF dice in format: `number of dice`d`bonus`b. No math operations are supported. Example: `!roll-asoiaf 5d1b`\n**!rand** - returns a random number from given range (inclusive). Example: `!rand 1,10`\n**!8ball**, **!eightball** - gives a random eightball answer.\n**!quote** - gives Thought of the Day.\n**!fortune**, **!literature**, **!riddle** - works like UNIX `fortunes` command, with dicts being separate.'
        elif message.content.startswith('!roll ') or message.content == '!roll':
            print('User %s (ID: %s, Server: %s) made a command %s' % (message.author.name, message.author.id, message.server, message.content))
            if message.content.strip() == '!roll':
                msg = '{0.author.mention} specified an invalid dice expression.'
            else:
                msg = await get_roll(message)
        elif message.content.startswith('!roll-traveller ') or message.content == '!roll-traveller' or message.content.startswith('!roll-trv ') or message.content == '!roll-trv':
            print('User %s (ID: %s, Server: %s) made a command %s' % (message.author.name, message.author.id, message.server, message.content))
            if message.content.strip() == '!roll':
                msg = '{0.author.mention} specified an invalid Traveller dice expression.'
            else:
                msg = await get_roll(message, True)
        elif message.content.startswith('!roll-sr ') or message.content == '!roll-sr':
            print('User %s (ID: %s, Server: %s) made a command %s' % (message.author.name, message.author.id, message.server, message.content))
            if message.content.strip() == '!roll-sr':
                msg = '{0.author.mention} specified an invalid Shadowrun dice expression.'
            else:
                msg = await get_shadowrun_roll(message)
        elif message.content.startswith('!roll-asoiaf ') or message.content == '!roll-asoiaf':
            print('User %s (ID: %s, Server: %s) made a command %s' % (message.author.name, message.author.id, message.server, message.content))
            if message.content.strip() == '!roll-asoiaf':
                msg = '{0.author.mention} specified an invalid ASOIAF dice expression.'
            else:
                msg = await get_asoiaf_roll(message)
        elif message.content.startswith('!roll-repeat ') or message.content == '!roll-repeat' or message.content.startswith('!roll-r ') or message.content == '!roll-r':
            print('User %s (ID: %s, Server: %s) made a command %s' % (message.author.name, message.author.id, message.server, message.content))
            if message.content.strip() == '!roll-repeat' or message.content.strip() == '!roll-r':
                msg = '{0.author.mention} specified an invalid repeated dice expression.'
            else:
                msg = await get_repeated_roll(message)
        elif message.content.startswith('!rand ') or message.content == '!rand':
            print('User %s (ID: %s, Server: %s) made a command %s' % (message.author.name, message.author.id, message.server, message.content))
            if message.content.strip() == '!rand':
                msg = '{0.author.mention} specified an invalid rand expression.'
            else:
                msg = await get_rand(message)
        elif message.content.startswith('!8ball ') or message.content.startswith('!eightball ') or message.content == '!8ball' or message.content == '!eightball':
            print('User %s (ID: %s, Server: %s) made a command %s' % (message.author.name, message.author.id, message.server, message.content))
            msg = '{0.author.mention}, 🎱 says: **%s**' % await get_eightball()
        elif message.content.startswith('!quoteoftheday ') or message.content.startswith('!quote ') or message.content.startswith('!thought ') or message.content.startswith('!thoughtoftheday ') or message.content == '!quoteoftheday' or message.content == '!quote' or message.content == '!thought' or message.content == '!thoughtoftheday':
            print('User %s (ID: %s, Server: %s) made a command %s' % (message.author.name, message.author.id, message.server, message.content))
            # This could be moved to a separate function
            date_now = datetime.datetime.now()
            if date_now.date() > CURRENT_QUOTE[1].date():
                with await QUOTE_LOCK:
                    #Check again after lock was lifted
                    if date_now.date() > CURRENT_QUOTE[1].date():
                        CURRENT_QUOTE = (await get_quote_of_the_day(QUOTES_FILE, QUOTES_LIST), date_now)
            # Easter egg for one server
            msg = '%sThought of the Day: **%s**' % ("Midwinter's " if int(message.server.id) == 389536986261618688 else "", CURRENT_QUOTE[0])
        # fortune module
        elif message.content.startswith('!fortune ') or message.content == '!fortune':
            print('User %s (ID: %s, Server: %s) made a command %s' % (message.author.name, message.author.id, message.server, message.content))
            msg = '{0.author.mention} 🔮 says:\n%s' % await get_fortune(FORTUNES_FILE, FORTUNES_LIST)
        elif message.content.startswith('!literature ') or message.content == '!literature':
            print('User %s (ID: %s, Server: %s) made a command %s' % (message.author.name, message.author.id, message.server, message.content))
            msg = '{0.author.mention} 📚:\n%s' % await get_fortune(LITERATURE_FILE, LITERATURE_LIST)
        elif message.content.startswith('!riddle ') or message.content == '!riddle':
            print('User %s (ID: %s, Server: %s) made a command %s' % (message.author.name, message.author.id, message.server, message.content))
            msg = '{0.author.mention} 🤔:\n%s' % await get_fortune(RIDDLES_FILE, RIDDLES_LIST)

        #GOOD BOY MODULE
        else:
            if CLIENT.user in message.mentions:
                if EXPLAIN_BOT_RE.search(message.content):
                    print('User %s (ID: %s, Server: %s) asked to explain %s' % (message.author.name, message.author.id, message.server, message.content))
                    await CLIENT.send_message(message.channel, "%s, %s" % (message.author.mention, random.choice(EXPLAIN).format(message)))
                    return
                if BAD_BOT_RE_MENTION.search(message.content):
                    print('User %s (ID: %s, Server: %s) made a bad bot comment :( %s' % (message.author.name, message.author.id, message.server, message.content))
                    await CLIENT.add_reaction(message, random.choice(BADBOYREACTIONS))
                    return
                if HIGH_FIVE_RE.search(message.content):
                    print('User %s (ID: %s, Server: %s) made a high five comment :( %s' % (message.author.name, message.author.id, message.server, message.content))
                    await CLIENT.add_reaction(message, "✋")
                    return
            if HIGH_FIVE_RE.search(message.content):
                async for item in CLIENT.logs_from(message.channel, limit=5, before=message):
                    if item.author == CLIENT.user:
                        print('User %s (ID: %s, Server: %s) made a high five comment :( %s' % (message.author.name, message.author.id, message.server, message.content))
                        await CLIENT.add_reaction(message, "✋")
                        return
            if BAD_BOT_RE.search(message.content):
                async for item in CLIENT.logs_from(message.channel, limit=5, before=message):
                    if item.author == CLIENT.user:
                        print('User %s (ID: %s, Server: %s) made a bad bot comment :( %s' % (message.author.name, message.author.id, message.server, message.content))
                        await CLIENT.add_reaction(message, random.choice(BADBOYREACTIONS))
                        return
            if CLIENT.user in message.mentions and GOOD_BOT_RE_MENTION.search(message.content):
                print('User %s (ID: %s, Server: %s) made a good bot comment :( %s' % (message.author.name, message.author.id, message.server, message.content))
                await CLIENT.add_reaction(message, random.choice(GOODBOYREACTIONS))
                return
            if GOOD_BOT_RE.search(message.content):
                async for item in CLIENT.logs_from(message.channel, limit=5, before=message):
                    if item.author == CLIENT.user:
                        print('User %s (ID: %s, Server: %s) made a good bot comment %s' % (message.author.name, message.author.id, message.server, message.content))
                        await CLIENT.add_reaction(message, random.choice(GOODBOYREACTIONS))
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
                await CLIENT.send_file(message.channel, image_file, content=temp_msg.format(message))
                await CLIENT.send_file(message.author, log_file)
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
                await CLIENT.send_file(message.channel, image_file, content=temp_msg.format(message))
                await CLIENT.send_file(message.author, log_file)
                os.remove(log_file)
                os.remove(image_file)

        if msg:
            print(msg)
            await CLIENT.send_message(message.channel, msg.format(message))
    except:
        # Catch anything
        print(traceback.format_exc())
        await CLIENT.send_message(message.channel, msg.format("Something went wrong! Please try again."))

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
