import subprocess
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings
from rapidfuzz import process, utils
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit import Application
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.buffer import Buffer
from modules.games.bottles import GameItem, get_bottle_games


def _game_item_processor(value: str | GameItem) -> str:
    if isinstance(value, GameItem):
        return value.label

    return utils.default_process(value) or ""

class Module:
    def __init__(self) -> None:
        pass

    def get_list(self) -> dict[str, GameItem]:
        return {}

    def take_action(self, item: GameItem):
        pass

class GameModule(Module):
    def __init__(self) -> None:
        super().__init__()
        self.modules: dict[str, Module] = {"bottles":BottlesModule()}
        self.data: dict[str, GameItem] = {}

    def get_list(self) -> dict[str, GameItem]:
        if len(self.data) > 1:
            return self.data
        else:
            for m in self.modules.values():
                res = m.get_list()
                self.data.update(res)
            return self.data

    def take_action(self, item: GameItem):
        module = self.modules.get(item.source)
        if module:
            module.take_action(item)
         
class BottlesModule(Module):
    def __init__(self) -> None:
        super().__init__()

    def get_list(self) -> dict[str, GameItem]:
        return get_bottle_games()
 
    def take_action(self, item: GameItem):
        subprocess.run([
            "bottles-cli",
            "run",
            "-b",
            item.meta["bottle"],
            "-p",
            item.meta["prog"],
        ])

MUSIC = [
    "Numb",
    "Bohemian Rhapsody",
    "Blinding Lights",
]


def get_music() -> dict[str, GameItem]:
    return {
        f"music:{name}": GameItem(
            key=f"music:{name}",
            label=name,
            source="music",
            meta={},
        )
        for name in MUSIC
    }

kb = KeyBindings()

@kb.add('c-c')
def exit_(event):
        event.app.exit()

class SearchList:
    def __init__(self) -> None:
        self.app : Application | None = None
        self.modules : dict[str, Module] = {"games": GameModule()}
        self.flag = ""
        self.current_item = 0
        self.selected = -1
        self.query = ""
        self.input_str = ""
        self.values: list[GameItem] = self.get_res(self.get_candidates(self.flag))
        self.control = FormattedTextControl(self.get_list_text)


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
                self.modules["games"].take_action(self.values[self.current_item])

    def parse_input(self):
        res = self.input_str.split("/", maxsplit=1)
        if len(res) == 2:
            if self.flag != res[0] and self.app:
                self.selected = -1
                self.current_item = 0
                self.app.invalidate()

            self.flag = res[0]
            self.query = res[1]
        else: 
            self.flag = ""
            self.query = res[0]

    def get_candidates(self, flag) -> dict[str, GameItem]:
        if not flag:
            return {}

        if flag == "g":
            gameModule = self.modules["games"]
            return gameModule.get_list()

        if flag == "m":
            return get_music()

        return {}

    def get_res(self, candidates: dict[str, GameItem]) -> list[GameItem]:
        cutoff = 40
        if not candidates:
            return []

        res = process.extract(
            self.query,
            list(candidates.values()),
            limit=20,
            score_cutoff=cutoff,
            processor=_game_item_processor
        )
        return [e[0] for e in res]

    def get_list_text(self):

        res = FormattedText([])

        for i, value in enumerate(self.values):
            if i == self.current_item:
                res.extend([("fg:#ff0088 bg:#474747 bold", "> "),("bg:#474747 bold", value.label)])
                
            else: 
                res.extend([("", " "),("", " "+value.label)])
            res.append(("", "\n"))
        return res
        

    def update(self, app:Application):
        self.parse_input()
        #no query case, show all the entries
        if len(self.flag) == 1 and len(self.query) < 1:
            self.values = list(self.get_candidates(self.flag).values())
        # query, show processed entries
        else: self.values = self.get_res(self.get_candidates(self.flag))
        app.invalidate()


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
        searchList.update(app)

    buffer1.on_text_changed += on_input_buffer_change 

    app.run()

if __name__ == "__main__":
    main()
