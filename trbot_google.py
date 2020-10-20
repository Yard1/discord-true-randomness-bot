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
    try:
        async with get_session(service, browser) as session:
            await session.get(f'https://www.google.com/search?hl=en&q={url_text}')
            try:
                await session.wait_for_element(2, 'div[aria-level="3"][role="heading"]')
                source = await session.get_page_source()
            except ArsenicTimeout:
                source = "NULL"
    except:
        pass
    msg = "Something went wrong."
    if source == "NULL":
        msg = "Sorry, I have no answer for this."
    else:
        try:
            soup = BeautifulSoup(source)
            expand_list = soup.find("div", {"class": "xpdopen"})
            if expand_list:
                expand_list.decompose()
            msg = soup.find("div", id="kp-wp-tab-cont-overview")
            if not msg:
                msg = soup.find("div", {"role" : "heading", "aria-level" : 3, "data-attrid": True})
            msg = msg.get_text(" ", strip=True)
        except:
            traceback.print_exc()
    return msg