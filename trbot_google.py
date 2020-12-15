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
    CHROME_OPTIONS["excludeSwitches"] = ['enable-automation']
    CHROME_OPTIONS["User-Agent"] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36"

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


@try_arsenic
async def get_kp_box(session):
    kp = await session.wait_for_element(1, 'div[class|="kp"]')
    kp_box = await kp.get_element('div[aria-level="3"][role="heading"][data-attrid]')
    try:
        kp_box = await kp_box.get_element("span")
    except NoSuchElement:
        pass
    return kp_box


@try_arsenic
async def get_kc_box_basic(session):
    kc_box = await session.get_element('div[data-attrid="description"]')
    return kc_box


@try_arsenic
async def get_kc_box_expanded(session):
    kc_box = await session.get_element(
        'div[data-attrid^="kc"]:not([data-attrid*="image"]) span:not([class])'
    )
    return kc_box


async def get_kc_box(session):
    kc_box = await get_kc_box_basic(session)
    if not kc_box:
        kc_box = await get_kc_box_expanded(session)
    return kc_box


async def get_google_answer_element(url_text):
    source = None
    msg = DEFAULT_MSG
    service = services.Chromedriver()
    browser = browsers.Chrome(**{"goog:chromeOptions": CHROME_OPTIONS})
    try:
        async with get_session(service, browser) as session:
            await session.get(f"https://www.google.com/search?hl=en&q={url_text}")
            kp_box = await get_kp_box(session)
            if kp_box:
                msg = await kp_box.get_text()
            if not (kp_box and msg):
                kc_box = await get_kc_box(session)
                if not kc_box:
                    source = "NULL"
                elif not source:
                    source = await kc_box.get_attribute("outerHTML")
                    msg = ""
    except:
        msg = DEFAULT_MSG
        traceback.print_exc()
    return (msg, source)


async def escape_markdown(str):
    if not str:
        return str
    return str.replace("`", "\\`").replace("*", "\\*").replace("_", "\\_")


async def get_google_answer(message):
    clean_message = message.content.replace("`", "").replace("!answer", "")
    url_text = TAG_RE.sub("", clean_message).strip().replace(" ", "+")
    msg, source = await get_google_answer_element(url_text)

    if not msg:
        if source == "NULL" or not source:
            msg = DEFAULT_MSG
        else:
            soup = BeautifulSoup(source)
            print(soup)
            links = [
                x["href"]
                for x in soup.find_all("a", attrs={"href": True})
                if "wikipedia" in x["href"]
            ]
            str_lst = [x.strip() for x in soup.stripped_strings]
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
    if not msg:
        msg = DEFAULT_MSG
    else:
        msg = await escape_markdown(msg)
    return msg