from modules.core import Module
from modules.music.ytmusic import YtMusicModule


class MusicModule(Module):
    def __init__(self) -> None:
        super().__init__()
        self.modules = {"ytmusic":YtMusicModule()}
    async def init(self):
        for m in self.modules.items():
            if m[0] == "ytmusic":
                await m[1]._get_chrome_wsURL()
    async def write_to_search(self, query):
        ytmusicModule = self.modules["ytmusic"]
        await ytmusicModule.write_to_search(query)

    async def get_suggestions(self, query):
        ytmusicModule = self.modules["ytmusic"]
        return await ytmusicModule.get_suggestions(query)

    async def get_search_results(self, query):
        ytmusicModule = self.modules["ytmusic"]
        return await ytmusicModule.get_search_results(query)

    async def take_action(self, item):
        ytmusicModule = self.modules["ytmusic"]
        return await ytmusicModule.take_action(item)
