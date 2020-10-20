import asyncio
import sys
import os

from arsenic import get_session, keys, browsers, services
from arsenic.errors import ArsenicTimeout

from bs4 import BeautifulSoup
from trbot import TAG_RE

CHROME_BINARY = os.getenv("GOOGLE_CHROME_SHIM")
CHROME_OPTIONS = {'args': ['--headless', '--disable-gpu']}
if CHROME_BINARY:
    CHROME_OPTIONS["binary"] = CHROME_BINARY

async def get_google_answer(message):
    url_text = TAG_RE.sub("", message.content.replace("`", "")).strip().replace(" ", "+")
    service = services.Chromedriver()
    browser = browsers.Chrome(chromeOptions=CHROME_OPTIONS)
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
    if not source:
        msg = "Something went wrong."
    elif source == "NULL":
        msg = "Sorry, I have no answer for this."
    else:
        soup = BeautifulSoup(source)
        msg = soup.find("div", {"role" : "heading", "aria-level" : 3}).get_text(" ", strip=True)
    return msg