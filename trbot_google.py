import asyncio
import sys
import os
import traceback

from arsenic import get_session, keys, browsers, services
from arsenic.errors import ArsenicTimeout, NoSuchElement

from bs4 import BeautifulSoup
from trbot import TAG_RE

CHROME_BINARY = os.getenv("GOOGLE_CHROME_SHIM")
CHROME_OPTIONS = {}
if CHROME_BINARY:
    CHROME_OPTIONS["binary"] = CHROME_BINARY

DEFAULT_MSG = "Sorry, I have no answer for this."


def try_arsenic(f):
    async def wrapper(*args, **kwargs):
        try:
            return await f(*args, **kwargs)
        except Exception as e:
            if not isinstance(e, ArsenicTimeout):
                print("CAUGHT EXCEPTION")
                traceback.print_exc()
                print("")
            return None

    return wrapper


async def format_kc_box_text(kc_box):
    source = await kc_box.get_attribute("outerHTML")
    if source == "NULL" or not source:
        msg = None
    else:
        soup = BeautifulSoup(source)
        print(soup)
        links = [
            x["href"]
            for x in soup.find_all("a", attrs={"href": True})
            if "wikipedia" in x["href"]
        ]
        str_lst = [await escape_markdown(x.strip()) for x in soup.stripped_strings]
        try:
            if str_lst[-1] == "More":
                str_lst = []
            else:
                if len(str_lst) > 1:
                    str_lst = str_lst[:-1]
                if str_lst[0] == "Description":
                    str_lst.pop(0)
                elif len(str_lst) > 1:
                    str_lst[0] = f"**{str_lst[0]}**"
                if links:
                    str_lst.append(links[0])
            msg = " ".join(str_lst)
        except:
            msg = None
    return msg


@try_arsenic
async def get_kp_box_text(session):
    kp = await session.get_element('div[class|="kp"]')
    kp_box = await kp.get_element('div[aria-level="3"][role="heading"][data-attrid]')
    try:
        kp_box_lst = await kp_box.get_elements(":scope > span")
        if len(kp_box_lst) < 2:
            kp_box = kp_box_lst[0]
        try:
            await kp_box_lst[0].get_element("svg")
            kp_box = kp_box_lst[1]
        except NoSuchElement:
            kp_box = kp_box_lst[0]
    except:
        pass

    try:
        return await kp_box.get_text()
    except:
        return None


@try_arsenic
async def get_kc_box_basic(session):
    kc_box = await session.get_element('div[data-attrid="description"]')
    return kc_box


@try_arsenic
async def get_kc_box_expanded(session):
    kc_box = await session.get_element(
        'div[data-attrid^="kc"]:not([data-attrid*="image"]):not([data-attrid*="music"]) span:not([class])'
    )
    return kc_box


@try_arsenic
async def get_stock_market(session):
    kc_box = await session.get_element("g-card-section")
    return kc_box


@try_arsenic
async def get_currency(session):
    kc_box = await session.get_element("div[data-exchange-rate]")
    return kc_box


async def get_kc_box_text(session):
    kc_box = await get_kc_box_basic(session)
    if not kc_box:
        kc_box = await get_kc_box_expanded(session)

    return await format_kc_box_text(kc_box)


async def get_financial_box_text(session):
    msg = None
    kc_box = await get_stock_market(session)
    if kc_box:
        msg = await kc_box.get_text()
        msg = await escape_markdown(msg)
        try:
            msg = msg.replace(" · Disclaimer", "").replace(">", "for").split("\n")
            msg = f"{msg[0]} ({msg[5]})\n**{msg[1]}** ({msg[2]})\n{msg[3]}\n{msg[4]}"
        except:
            msg = None
    else:
        kc_box = await get_currency(session)
        if kc_box:
            msg = await kc_box.get_text()
            msg = await escape_markdown(msg)
            msg = msg.replace("\n", " ")
    return msg


async def get_google_answer_text(url_text):
    msg = None
    service = services.Chromedriver()
    browser = browsers.Chrome(**{"goog:chromeOptions": CHROME_OPTIONS})
    try:
        async with get_session(service, browser) as session:
            await session.get(f"https://www.google.com/search?hl=en&gl=UK&q={url_text}")
            msg = await get_financial_box_text(session)
            if not msg:
                msg = await get_kp_box_text(session)
            if not msg:
                msg = await get_kc_box_text(session)
    except:
        msg = None
        traceback.print_exc()
    return msg


async def escape_markdown(str):
    if not str:
        return str
    return str.replace("`", "\\`").replace("*", "\\*").replace("_", "\\_")


async def get_google_answer(message):
    clean_message = message.content.replace("`", "").replace("!answer", "")
    url_text = TAG_RE.sub("", clean_message).strip().replace(" ", "+")
    msg = await get_google_answer_text(url_text)
    if not msg:
        msg = DEFAULT_MSG
    return msg