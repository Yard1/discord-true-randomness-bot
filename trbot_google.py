import asyncio
import sys
import os
import traceback

from arsenic import get_session, keys, browsers, services
from arsenic.errors import ArsenicTimeout

from bs4 import BeautifulSoup
from trbot import TAG_RE

CHROME_BINARY = os.getenv("GOOGLE_CHROME_SHIM")
CHROME_OPTIONS = {}
if CHROME_BINARY:
    CHROME_OPTIONS["binary"] = CHROME_BINARY

async def get_google_answer(message):
    url_text = TAG_RE.sub("", message.content.replace("`", "")).strip().replace(" ", "+")
    service = services.Chromedriver()
    browser = browsers.Chrome(**{"goog:chromeOptions":CHROME_OPTIONS})
    source = None
    msg = "Sorry, I have no answer for this."
    try:
        async with get_session(service, browser) as session:
            #await session.set_window_size(1920, 1080)
            await session.get(f'https://www.google.com/search?hl=en&q={url_text}')
            a = None
            b = None
            try:
                kp = await session.wait_for_element(1, 'div[class|="kp"')
                a = await kp.get_element('div[aria-level="3"][role="heading"][data-attrid]')
            except:
                traceback.print_exc()
            if a:
                msg = await a.get_text()
            if a and msg:
                pass
            else:
                try:
                    b = await session.wait_for_element(1, 'div[data-attrid="description"]')
                except:
                    traceback.print_exc()
                if not a and not b:
                    source = "NULL"
                if not source:
                    source = await b.get_attribute("outerHTML")
                    msg = ""
    except:
        msg = "Sorry, I have no answer for this."
        traceback.print_exc()
    if not msg:
        if source == "NULL" or not source:
            msg = "Sorry, I have no answer for this."
        else:
            soup = BeautifulSoup(source)
            str_lst = [x.strip() for x in soup.stripped_strings][:-1]
            if str_lst[0] in ("Description", "Lyrics", "Videos"):
                str_lst.pop(0)
            else:
                str_lst[0] = f"**{str_lst[0]}**"
            msg = " ".join(str_lst)
    if not msg:
        msg = "Sorry, I have no answer for this."
    return msg