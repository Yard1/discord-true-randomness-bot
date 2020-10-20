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

DEFAULT_MSG = "Sorry, I have no answer for this."


async def get_google_answer(message):
    url_text = (
        TAG_RE.sub("", message.content.replace("`", "").replace("!answer", ""))
        .strip()
        .replace(" ", "+")
    )
    service = services.Chromedriver()
    browser = browsers.Chrome(**{"goog:chromeOptions": CHROME_OPTIONS})
    source = None
    msg = DEFAULT_MSG
    try:
        async with get_session(service, browser) as session:
            await session.get(f"https://www.google.com/search?hl=en&q={url_text}")
            a = None
            b = None
            try:
                kp = await session.wait_for_element(1, 'div[class|="kp"]')
                a = await kp.get_element(
                    'div[aria-level="3"][role="heading"][data-attrid]'
                )
                a = await a.get_element("span")
            except Exception as e:
                if not isinstance(e, ArsenicTimeout):
                    traceback.print_exc()
            if a:
                msg = await a.get_text()
            if a and msg:
                pass
            else:
                try:
                    b = await session.wait_for_element(
                        1, 'div[data-attrid="description"]'
                    )
                except Exception as e:
                    if not isinstance(e, ArsenicTimeout):
                        traceback.print_exc()
                    try:
                        b = await session.wait_for_element(
                            1, 'div[data-attrid^="kc"]:not([data-attrid*="image"]) span:not([class])'
                        )
                    except Exception as e:
                        if not isinstance(e, ArsenicTimeout):
                            traceback.print_exc()
                if not a and not b:
                    source = "NULL"
                if not source:
                    source = await b.get_attribute("outerHTML")
                    msg = ""
    except:
        msg = DEFAULT_MSG
        traceback.print_exc()
    if not msg:
        if source == "NULL" or not source:
            msg = DEFAULT_MSG
        else:
            soup = BeautifulSoup(source)
            links = [
                x["href"]
                for x in soup.find_all("a", attrs={"href": True})
                if "wikipedia" in x["href"]
            ]
            str_lst = [x.strip() for x in soup.stripped_strings]
            if len(str_lst) > 1:
                str_lst = str_lst[:-1]
            if str_lst[0] in ("Description", "Lyrics", "Videos"):
                str_lst.pop(0)
            elif len(str_lst) > 1:
                str_lst[0] = f"**{str_lst[0]}**"
            if links:
                str_lst.append(links[0])
            msg = " ".join(str_lst)
    if not msg:
        msg = DEFAULT_MSG
    return msg