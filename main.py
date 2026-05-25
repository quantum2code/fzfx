from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings
from rapidfuzz import process, utils
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit import Application
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.buffer import Buffer
import asyncio
from modules.core import Module, SearchItem
from modules.games.core import GameModule
from modules.music.core import MusicModule

def _game_item_processor(value: str | SearchItem) -> str:
    if isinstance(value, SearchItem):
        return value.label.lower()

    return utils.default_process(value) or ""

kb = KeyBindings()

@kb.add('c-c')
def exit_(event):
        event.app.exit()

class SearchList:
    def __init__(self) -> None:
        self.app : Application | None = None
        self.modules : dict[str, Module] = {"games": GameModule(), "music": MusicModule()}
        self.update_task: asyncio.Task | None = None
        self.flag = ""
        self.current_item = 0
        self.selected = -1
        self.query = ""
        self.input_str = ""
        self.values: list[SearchItem] =  []       
        self.control = FormattedTextControl(self.format_values)


        @kb.add('up')
        def _up(event):
            if len(self.values) and self.current_item > 0:
                self.current_item = self.current_item - 1

            else: self.current_item = len(self.values)-1
        @kb.add('down')
        def _down(event):
            if len(self.values) and self.current_item < len(self.values)-1:
                self.current_item = self.current_item + 1

            else: self.current_item = 0

        @kb.add('enter')
        def _select(event):
            self.selected = self.current_item
            if len(self.values) and 0 <= self.current_item < len(self.values):
                item = self.values[self.current_item]
                match self.flag:
                    case "m":
                        action = self.modules["music"].take_action(item)
                    case "g":
                        action = self.modules["games"].take_action(item)
                    case _:
                        action = None
                if asyncio.iscoroutine(action):
                    asyncio.create_task(action)

    async def parse_input(self):
        res = self.input_str.split("/", maxsplit=1)
        if len(res) == 2:
            if self.flag != res[0] and self.app:
                self.selected = -1
                self.current_item = 0
                if res[0] == "m":
                    m = self.modules["music"]
                    await m.init()
                self.app.invalidate()

            self.flag = res[0]
            self.query = res[1]
        else: 
            self.flag = ""
            self.query = res[0]

    async def get_candidates(self, flag) -> list[SearchItem]:
        if not flag:
            return []

        if flag == "g":
            gameModule = self.modules["games"]
            return gameModule.get_list()

        if flag == "m":
            musicModule = self.modules["music"]
            res = await musicModule.get_list()
            return res
        return []

    def get_res(self, candidates: list[SearchItem]) -> list[SearchItem]:
        cutoff = 40
        if not candidates:
            return []

        res = process.extract(
            self.query,
            candidates,
            limit=20,
            score_cutoff=cutoff,
            processor=_game_item_processor
        )
        return [e[0] for e in res]

    def format_values(self):

        res = FormattedText([])

        for i, value in enumerate(self.values):
            if i == self.current_item:
                res.extend([("fg:#ff0088 bg:#474747 bold", "> "),("bg:#474747 bold", value.label)])
                
            else: 
                res.extend([("", " "),("", " "+value.label)])
            res.append(("", "\n"))
        return res
        

    async def update(self, app:Application):
        try:
            await self.parse_input()
            match(self.flag):
                case "g":
                    #no query case, show all the entries
                    if len(self.flag) == 1 and len(self.query) < 1:
                        self.values = await self.get_candidates(self.flag)
                    # query, show processed entries
                    else: 
                        candidates = await self.get_candidates(self.flag)
                        self.values = self.get_res(candidates)
                case "m":
                    musicModule = self.modules["music"]
                    await musicModule.write_to_search(self.query)
                    await asyncio.sleep(0.35)
                    candidates = await self.get_candidates(self.flag)
                    self.values = candidates
            app.invalidate()
        except asyncio.CancelledError:
            return


def main():
    searchList = SearchList()
    buffer1 = Buffer()

    root_container = HSplit([

        Window(content=searchList.control),

        Window(height=1, char='-' ),

        Window(height=5,content=BufferControl(buffer=buffer1, focus_on_click=True)),

        ])

    layout = Layout(root_container)

    app = Application(layout=layout, full_screen=True, key_bindings=kb, mouse_support=True)

    searchList.app = app

    def on_input_buffer_change(buf:Buffer):
        searchList.input_str = buf.text
        if searchList.update_task and not searchList.update_task.done():
            searchList.update_task.cancel()
        searchList.update_task = asyncio.create_task(searchList.update(app))

    buffer1.on_text_changed += on_input_buffer_change 

    app.run()

if __name__ == "__main__":
    main()
