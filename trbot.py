#!/usr/bin/python3
# -*- coding: utf-8 -*-
import matplotlib
matplotlib.use('Agg')
import traceback
import re
import random
import operator
from asteval import Interpreter
import sourcerandom
from sourcerandom import OnlineRandomnessSource
from wordcloud import WordCloud
import datetime
import os
import zipfile

AEVAL = Interpreter()
QUOTES_FILE = 'quotes.txt'
QUOTES_LIST = []
FORTUNES_FILE = "fortunes.txt"
FORTUNES_LIST = []
LITERATURE_FILE = "literature.txt"
LITERATURE_LIST = []
RIDDLES_FILE = "riddles.txt"
RIDDLES_LIST = []

CURRENT_QUOTE = ("", None)

# Randomness module
RANDOM_BYTES_COUNT = 1024
MAX_RANGE = 4294967295  #2**32 - 1
RAND_GEN = sourcerandom.SourceRandom(source=OnlineRandomnessSource.RANDOM_ORG, cache_size=RANDOM_BYTES_COUNT, preload=True)

# Regex
DICE_RE = re.compile(r"[0-9]*d[0-9]*", re.IGNORECASE)
SHADOWRUN_DICE_RE = re.compile(r"([0-9]*)d?\s*>=?\s*([0-9]*)", re.IGNORECASE)
OPERATOR_RE = re.compile(r"[\+\-\^\*\%\/]", re.IGNORECASE)
COMPARATOR_RE = re.compile(r"(?:[<>][=]?)|(?:==)", re.IGNORECASE)
GOOD_BOT_RE = re.compile(r"((?:\bwise)|(?:smart)|(?:cutie)|(?:cute)|(?:fun)|(?:great)|(?:\bintelligent)|(?:\bgood)|(?:nice)|(?:amazing)|(?:gud)|(?:lovely)|(?:pretty)|(?:useful)|(?:best)|(?:love you)|(?:love u)|(?:luv u)|(?:luv you))\s*((?:bot)|(?:boy)|(?:boi)|(?:botty))", re.IGNORECASE)
GOOD_BOT_RE_MENTION = re.compile(r"(?:\bwise)|(?:smart)|(?:cutie)|(?:cute)|(?:\bqt\b)|(?:you are better)|(?:you're better)|(?:u are better)|(?:you are nicer)|(?:you're nicer)|(?:u are nicer)|(?:fun)|(?:\bintelligent)|(?:great)|(?:\bgood)|(?:nice)|(?:amazing)|(?:gud)|(?:lovely)|(?:pretty)|(?:useful)|(?:best)|(?:love)|(?:luv)", re.IGNORECASE)
BAD_BOT_RE = re.compile(r"((?:suicide)|(?:ghey)|(?:gay)|(?:nasty)|(?:piss)|(?:turd)|(?:poop)|(?:shit)|(?:ungood)|(?:bad)|(?:no fun)|(?:dumb)|(?:worst)|(?:terrible)|(?:horrible)|(?:stinky)|(?:mean)|(?:rude)|(?:cunt)|(?:moron)|(?:ass)|(?:fuck)|(?:fuck\s*you)|(?:fuck\s*u)|(?:kill\s*yourself)|(?:kys))\s*((?:bot)|(?:boy)|(?:boi)|(?:botty))", re.IGNORECASE)
BAD_BOT_RE_MENTION = re.compile(r"(?:suicide)|(?:ghey)|(?:gay)|(?:nasty)|(?:piss)|(?:turd)|(?:poop)|(?:shit)|(?:ungood)|(?:bad)|(?:no fun)|(?:dumb)|(?:worst)|(?:terrible)|(?:horrible)|(?:stinky)|(?:mean)|(?:rude)|(?:cunt)|(?:moron)|(?:ass)|(?:fuck)|(?:fuck\s*you)|(?:fuck\s*u)|(?:kill\s*yourself)|(?:kys)|(?:go\s*to\s*hell)", re.IGNORECASE)
EXPLAIN_BOT_RE = re.compile(r"(?:how)|(?:explain)|(?:explanation)|(?:why)|(?:what)|(?:tell)", re.IGNORECASE)
MATH_EXPRESSION_RE = re.compile(r"^[0-9\.\+\-\/\*\^\%\(\)\s]+$")
WORD_CLOUD_RE = re.compile(r"(\<\@[0-9]*?\>)|(\:(.*?)\:)")

# Lists
EIGHTBALL = [
    'It is certain',
    'It is decidedly so',
    'Without a doubt',
    'Yes definitely',
    'You may rely on it',
    'As I see it, yes',
    'Most likely',
    'Outlook good',
    'Yes',
    'Signs point to yes',
    'Reply hazy try again',
    'Ask again later',
    'Better not tell you now',
    'Cannot predict now',
    'Concentrate and ask again',
    'Don\'t count on it',
    'My reply is no',
    'My sources say no',
    'Outlook not so good',
    'Very doubtful']

EXPLAIN = [
    'I am impartial, boss!',
    'It\'s atmospheric noise!',
    'I am just a messenger!',
    'Blame the author!',
    'You win some, you lose some!',
    'That\'s just fate at work, man!',
    'I work hard to provide you with random numbers!',
    'RANDOM.ORG, baby. Atmospheric noise.',
    'I have no agenda.',
    'No gods, no masters, only bots.',
    'True randomness.',
    'https://www.random.org/analysis/dilbert.jpg']

GOODBOYREACTIONS = ['😀', '😁', '😄', '😉', '😇', '😊', '☺', '😌', '😍', '😘', '😚', '🤗', '❤']

BADBOYREACTIONS = ['😐', '😞', '😟', '😔', '😕', '☹', '😣', '😖', '😨', '😰', '😧', '😢', '😭']

COMPARATORS = {
    '>': operator.gt,
    '>=': operator.ge,
    '<': operator.lt,
    '<=': operator.le,
    '==': operator.eq}

# Functions
async def get_random_numbers(count, lo, hi):
    '''Main function to get a list of count random numbers from range lo to hi (inclusive)'''
    print("Roll %s * (%s - %s)" % (count, lo, hi))
    if lo > hi:
        raise ValueError('lo %s bigger than hi %s!' % (lo, hi))
    if hi >= MAX_RANGE:
        raise ValueError('hi %s bigger than MAX_RANGE %s!' % hi)
    if lo == hi:
        return [lo] * count
    try:
        list_to_return = []
        for _ in range(count):
            try:
                list_to_return.append(RAND_GEN.randint(lo, hi))
            except:
                # Use regular Python PRNG from random package if true randomness is unavailable
                print('Python PRNG in list')
                list_to_return.append(random.randint(lo, hi))
        return list_to_return
    except:
        # Use regular Python PRNG from random package if true randomness is unavailable
        print(traceback.format_exc())
        print('Python PRNG')
        return [random.randint(lo, hi) for _ in range(count)]

async def eval_math_expression(expression):
    '''Safely evaluate math expressions using asteval'''
    expression = expression.replace("^", "**")
    if not MATH_EXPRESSION_RE.match(expression):
        raise ValueError('Unallowed sign in expression!')
    evaluated_expression = AEVAL(expression)
    if evaluated_expression is None:
        raise ValueError('Exception in asteval')
    return evaluated_expression

async def parse_message(message):
    '''Change a string to a parsed one'''
    parsed_message = message.strip().replace(" ", "")
    return parsed_message

async def check_comparators(message):
    '''Check if the roll is a comparison (eg. X > Y) and handle'''
    comparator_match = COMPARATOR_RE.findall(message)
    if len(comparator_match) > 1:
        raise ValueError('Too many comparators!')
    return comparator_match

class DiceRoll:
    def __init__(self, dice_tuple, roll_val):
        self.dice_tuple = dice_tuple
        self.roll_val = roll_val

async def get_dices(parsed_message):
    '''Replace all dices expression in a string with generated numbers'''
    dices = []
    get_randomness = {}
    for match in DICE_RE.findall(parsed_message):
        split_match = match.split("d")
        split_match[0] = int(split_match[0])
        split_match[1] = int(split_match[1])

        dices.append(DiceRoll((split_match[0], split_match[1]), 0))
        if split_match[1] in get_randomness:
            get_randomness[split_match[1]] += split_match[0]
        else:
            get_randomness[split_match[1]] = split_match[0]

    for key, value in get_randomness.items():
        numbers = await get_random_numbers(value, 1, key)
        #print(numbers)
        for dice in dices:
            if not dice.roll_val and dice.dice_tuple[1] == key:
                for _ in range(0, dice.dice_tuple[0]):
                    dice.roll_val += numbers.pop()


    for dice in dices:
        parsed_message = DICE_RE.sub("%s" % dice.roll_val, parsed_message, 1)

    return parsed_message

# Commands
async def get_roll(message):
    '''Handles the !roll command'''
    if not isinstance(message, str):
        message = message.content
    message = message.replace("`", "")
    try:
        split_message = message.split(" ", 1)
        msg = ""
        parsed_message = await parse_message(split_message[1])
        parsed_message = await get_dices(parsed_message)
        msg = await handle_rolls(parsed_message.split(","), message)
    except:
        print(traceback.format_exc())
        msg = '.{0.author.mention} specified an invalid dice expression.'
    return msg[1:]

async def handle_rolls(rolls_list, message):
    print(rolls_list)
    msg = ""
    for item in rolls_list:
        comparator_match = await check_comparators(item)
        if comparator_match:
            item = item.split(comparator_match[0])
            item = [await get_dices(item[0]), comparator_match[0], await get_dices(item[1])]
        if isinstance(item, list):
            # Is a comparison - two expressions separated by a comparison operator
            item[0] = await eval_math_expression(item[0])
            item[2] = await eval_math_expression(item[2])
            result = str(item[0])
            result += ' ' + str(item[1]) + ' '
            result += str(item[2])
            print(result)
        else:
            result = (str(await eval_math_expression(item)), OPERATOR_RE.search(item))
        if isinstance(item, list):
            print(COMPARATORS[item[1]](item[0], item[2]))
            msg += '\n{0.author.mention} has **%s**. (`%s`)' % ('succeeded' if COMPARATORS[item[1]](item[0], item[2]) else 'failed', result)
        else:
            msg += '\n{0.author.mention} %s **%s**.' % ('rolled' if DICE_RE.search(message) else 'got', round(float(result[0]), 1) if '.' in str(result[0]) else result[0])
            if result[1]:
                msg += ' (`%s`)' % item
    return msg

async def get_repeated_roll(message):
    if not isinstance(message, str):
        message = message.content
    message = message.replace("`", "")
    try:
        split_message = message.split(" ", 1)
        msg = ""
        parsed_message = await parse_message(split_message[1])
        parsed_message = parsed_message.split(",")
        if len(parsed_message) != 2:
            raise ValueError("Wrong number of arguments")
        repeat = int(parsed_message[1])
        print(parsed_message)
        print(repeat)
        repeated_list = ",".join([parsed_message[0]] * repeat)
        print(repeated_list)
        parsed_message = await get_dices(repeated_list)
        print(parsed_message)
        msg = await handle_rolls(parsed_message.split(","), message)
    except:
        print(traceback.format_exc())
        msg = '.{0.author.mention} specified an invalid dice expression.'
    return msg[1:]

async def get_shadowrun_roll(message):
    '''Handles the !roll-sr command'''
    if not isinstance(message, str):
        message = message.content
    message = message.replace("`", "")
    try:
        split_message = message.split(" ", 1)
        msg = ""
        parsed_message = await parse_message(split_message[1])
        for item in parsed_message.split(","):
            sr_match = SHADOWRUN_DICE_RE.match(item.strip())
            if not sr_match:
                raise ValueError('Wrong Shadowrun dice expression.')
            dices = int(sr_match.group(1))
            required_successes = int(sr_match.group(2))
            results = await get_shadowrun_dices(dices)
            success = results[1] >= required_successes
            glitch = results[2] > dices // 2
            
            if success and not glitch:
                has_msg = 'Succeeded'
            elif glitch:
                if success < 1:
                    has_msg = 'Critically Glitched'
                else:
                    has_msg = 'Glitched'
            else:
                has_msg = 'Failed'

            msg += '\n{0.author.mention} has **%s**! (Dices: `%d`, Hits: `%d %s %d`, 1s: `%d %s %d`)\n```%s```' % (has_msg, dices, results[1], '≥' if success else '<', required_successes, results[2], '>' if glitch else '≤', dices // 2, results[0]) 
    except:
        print(traceback.format_exc())
        msg = '.{0.author.mention} specified an invalid Shadowrun dice expression.'
    return msg[1:]

async def get_shadowrun_dices(number_of_dices):
    successes = 0
    failures = 0
    dices = await get_random_numbers(number_of_dices, 1, 6)
    dices.sort(reverse=True)
    for dice in dices:
        if dice >= 5:
            successes += 1
        elif dice == 1:
            failures += 1
    return (dices, successes, failures)

async def get_rand(message):
    '''Handles the !rand command'''
    if not isinstance(message, str):
        message = message.content
    message = message.replace("`", "")
    try:
        split_message = message.split(" ", 1)
        msg = ""
        split_message = split_message[1].split(",")
        if len(split_message) > 2:
            raise ValueError('Too many arguments.')
        random_numbers = await get_random_numbers(1, int(split_message[0]), int(split_message[1]))
        msg = '{0.author.mention}, your random number is **%s**.' % random_numbers[0]
    except:
        print(traceback.format_exc())
        msg = '{0.author.mention} specified an invalid rand expression.'
    return msg

async def get_eightball():
    '''Handles the !8ball command'''
    random_numbers = await get_random_numbers(1, 0, len(EIGHTBALL)-1)
    return EIGHTBALL[random_numbers[0]]

async def get_quote_of_the_day(name, quotes_list):
    '''Gets the quote of the day from file'''
    if not quotes_list:
        print("Reading file %s" % name)
        with open(name, "r") as f:
            quotes_list = f.read().splitlines()
    return random.choice(quotes_list)

async def get_fortune(name, fortune_list):
    '''Gets a fortune from file'''
    if not fortune_list:
        print("Reading file %s" % name)
        with open(name, "r") as f:
            fortune_list = f.read().split("%")
        fortune_list = [x.strip() for x in fortune_list if len(x.strip()) <= 2000] #2k characters Discord message limit
    return random.choice(fortune_list)

async def get_text_from_channels(channels, client, size=80, users=None):
    if users:
        print("Getting text from %s for users %s" % ([x.name for x in channels], [x for x in users]))
    else:
        print("Getting text from %s" % [x.name for x in channels])
    messages = []
    for channel in channels:
        async for message in client.logs_from(channel, limit=10000000):
            if users:
                if message.author.name in users:
                    messages.append(message)
            else:
                messages.append(message)
    messages_content = [x.content for x in sorted(messages, key=lambda x: x.timestamp)]
    print("There were %s messages" % str(len(messages_content)))
    if not messages_content:
        return
    image_file = await (create_wordcloud(''.join(WORD_CLOUD_RE.sub("", x).replace("_", "").replace("*", "").replace("`", "") for x in messages_content), size))
    log_file = 'log_%s' % datetime.datetime.now().isoformat()
    with open(log_file, 'w') as file:
        file.writelines(line + "\n\n" for line in messages_content)
    zipfile.ZipFile('%s.zip' % log_file, mode='w', compression=zipfile.ZIP_DEFLATED).write(log_file)
    os.remove(log_file)
    return (len(messages_content), image_file, '%s.zip' % log_file)


async def create_wordcloud(text, size=-1):
    filename = 'wordcloud_%s.png' % datetime.datetime.now().isoformat()
    if size > 0:
        WordCloud(width=1600, height=800, max_font_size=size).generate(text).to_file(filename)
    else:
        WordCloud(width=1600, height=800).generate(text).to_file(filename)
    return filename