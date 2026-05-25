import asyncio
import logging
from modules.core import Module, SearchItem
from modules.music.utils.ytmusic import get_suggestions_api, get_suggestions_dom, _search_songs_api, toSearchItem, write_to_search_dom, _send_cdp
import websockets
import subprocess
import httpx

logger = logging.getLogger("fzfx.music")

PORT=9222
yt_url="https://music.youtube.com"

class YtMusicModule(Module):
    def __init__(self) -> None:
        super().__init__()
        self.chromewsURL: str = ""

    async def _try_get_wsurl(self):
        try:
            res = httpx.get(f'http://localhost:{PORT}/json/list')
            if res.status_code == 200:
                resjson = res.json()
                wsurl = ""
                for i in list(resjson):
                    if i["title"] and yt_url in i["url"]:
                        wsurl = i["webSocketDebuggerUrl"]
                        break
                if wsurl:
                    try:
                        async with websockets.connect(wsurl) as ws:
                            await ws.send('{"id":1,"method":"Browser.getVersion"}')
                            await ws.recv()
                            self.chromewsURL = wsurl
                            return wsurl
                    except:
                        return ""
        except (httpx.RequestError, OSError, websockets.WebSocketException):
            return ""

    async def _get_chrome_wsURL(self):
        res = await self._try_get_wsurl()
        if res:
            self.chromewsURL = res
            return res

        if await self._init_chrome():
            for _ in range(3):
                await asyncio.sleep(0.5)
                res = await self._try_get_wsurl()
                if res:
                    self.chromewsURL = res
                    return res
        return ""

    async def _init_chrome(self):
        try:
            subprocess.Popen(["google-chrome",
                              "--user-data-dir=/home/qcode/.chrome-profiles/ytmusic/", 
                              f"--remote-debugging-port={PORT}", 
                              "--autoplay-policy=no-user-gesture-required", 
                              "--app=https://music.youtube.com", 
                              "--headless=new", 
                              "--audio-output-channels=2", 
                              "--user-agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'"],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
            return True

        except OSError:
            return False

    async def get_suggestions(self, query) -> list[SearchItem]:
        wsurl = await self._try_get_wsurl()
        if not wsurl:
            return []

        items = await get_suggestions_api(wsurl, query)

        return toSearchItem(items)

    async def get_search_results(self, query) -> list[SearchItem]:
        wsurl = await self._try_get_wsurl()
        if not wsurl:
            return []

        items = await _search_songs_api(wsurl, query)

        return toSearchItem(items)

    async def write_to_search(self, query:str):
        wsurl = await self._try_get_wsurl()
        if not wsurl:
            return
        await write_to_search_dom(wsurl, query)

    async def take_action(self, item: SearchItem) -> list[SearchItem] | None:
        url = item.meta.get("url")
        if (not isinstance(url, str) or not url):
            logger.debug("take_action invalid meta")
            return None

        wsurl = await self._try_get_wsurl()
        if not wsurl:
            logger.debug("take_action no wsurl")
            return None

        if "autoplay=" not in url:
            url = f"{url}&autoplay=1" if "?" in url else f"{url}?autoplay=1"


        async with websockets.connect(wsurl) as ws:
            logger.debug("take_action navigating song url=%s", url)
            await _send_cdp(ws, {
                "id": 3,
                "method": "Page.navigate",
                "params": {"url": url},
            })
        return None
