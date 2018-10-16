#!/usr/bin/python3
# -*- coding: utf-8 -*-
import re
import random
import datetime
import asyncio
import discord
from trbot import *

QUOTE_LOCK = asyncio.Lock()

async def on_message(message):
    global CURRENT_QUOTE
    try:

        msg = ""

        if message == '!help' or (re.search("help", message, re.IGNORECASE)):
            msg = 'List of commands:\n**!roll** - gives random dice rolls and calculates the resulting mathematical expression. Example: `!roll (1d100+10)/10`\n**!rand** - returns a random number from given range (inclusive). Example: `!rand 1,10`\n**!8ball**, **!eightball** - gives a random eightball answer.\n**!quote** - gives Thought of the Day.\n**!fortune**, **!literature**, **!riddle** - works like UNIX `fortunes` command, with dicts being separate.'
        elif message.startswith('!roll ') or message == '!roll':
            if message.strip() == '!roll':
                msg = 'specified an invalid dice expression.'
            else:
                msg = await get_roll(message)
        elif message.startswith('!rand ') or message == '!rand':
            if message.strip() == '!rand':
                msg = 'specified an invalid rand expression.'
            else:
                msg = await get_rand(message)
        elif message.startswith('!8ball ') or message.startswith('!eightball ') or message == '!8ball' or message == '!eightball':
            msg = '🎱 says: **%s**' % await get_eightball()
        elif message.startswith('!quoteoftheday ') or message.startswith('!quote ') or message.startswith('!thought ') or message.startswith('!thoughtoftheday ') or message == '!quoteoftheday' or message == '!quote' or message == '!thought' or message == '!thoughtoftheday':
            date_now = datetime.datetime.now()
            if date_now.date() > CURRENT_QUOTE[1].date():
                with await QUOTE_LOCK:
                    #Check again after lock was lifted
                    if date_now.date() > CURRENT_QUOTE[1].date():
                        CURRENT_QUOTE = (await get_quote_of_the_day(QUOTES_FILE, QUOTES_LIST), date_now)
            msg = 'Thought of the Day: **%s**' % CURRENT_QUOTE[0]
        elif message.startswith('!fortune ') or message == '!fortune':
            msg = '🔮 says:\n%s' % await get_fortune(FORTUNES_FILE, FORTUNES_LIST)
        elif message.startswith('!literature ') or message == '!literature':
            msg = '📚:\n%s' % await get_fortune(LITERATURE_FILE, LITERATURE_LIST)
        elif message.startswith('!riddle ') or message == '!riddle':
            msg = '🤔:\n%s' % await get_fortune(RIDDLES_FILE, RIDDLES_LIST)

        #GOOD BOY MODULE
        elif EXPLAIN_BOT_RE.search(message):
            msg = random.choice(EXPLAIN)
        elif BAD_BOT_RE.search(message):
            msg = random.choice(BADBOYREACTIONS)
        elif GOOD_BOT_RE.search(message):
            msg = random.choice(GOODBOYREACTIONS)

        if msg:
            print(msg)
    except:
        print(traceback.format_exc())
        print("Something went wrong! Please try again.")

async def on_ready():
    global CURRENT_QUOTE
    await get_fortune(FORTUNES_FILE, FORTUNES_LIST)
    await get_fortune(LITERATURE_FILE, LITERATURE_LIST)
    await get_fortune(RIDDLES_FILE, RIDDLES_LIST)
    CURRENT_QUOTE = (await get_quote_of_the_day(QUOTES_FILE, QUOTES_LIST), datetime.datetime.now())


loop = asyncio.get_event_loop()
results = loop.run_until_complete(on_ready())

while True:
    results = loop.run_until_complete(on_message(input(">")))

loop.close()