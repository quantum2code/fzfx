from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings
from rapidfuzz import process
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit import Application
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.buffer import Buffer
from modules.games.bottles import get_bottle_games


GAMES = [
    "Portal",
    "Half-Life",
    "Celeste",
    "Hades",
]

MUSIC = [
    "Numb",
    "Bohemian Rhapsody",
    "Blinding Lights",
]


def get_games():
    if len(GAMES) > 5:
        return GAMES
    GAMES.extend(get_bottle_games())
    return GAMES


def get_music():
    return MUSIC

kb = KeyBindings()

@kb.add('c-c')
def exit_(event):
        event.app.exit()

class SearchList:
    def __init__(self) -> None:
        self.app : Application | None = None
        self.flag = ""
        self.current_item = 0
        self.selected = -1
        self.query = ""
        self.input_str = ""
        self.values = self.format_list(self.get_res(self.get_candidates(self.flag)))
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

    def parse_input(self):
        res = self.input_str.split("/", maxsplit=1)
        if len(res) == 2:
            if self.flag != res[0] and self.app:
                self.app.invalidate()

            self.flag = res[0]
            self.query = res[1]
        else: 
            self.flag = ""
            self.query = res[0]

    def get_candidates(self, flag):
        if not flag:
            return []

        if flag == "g":
            return get_games()

        if flag == "m":
            return get_music()

        return []

    def get_res(self, candidates):
        return process.extract(
                self.query,
                candidates,
                limit=20,
            )
    def format_list(self,qlist):
        res = []
        for e in qlist:
            res.append(e[0])
        return res

    def get_list_text(self):

        res = FormattedText([])

        for i, value in enumerate(self.values):
            if i == self.current_item:
                res.extend([("fg:#ff0088 bg:#474747 bold", "> "),("bg:#474747 bold", value)])
                
            else: 
                res.extend([("", " "),(""," "+value)])
            res.append(("", "\n"))
        return res
        

    def update(self, app:Application):
        self.parse_input()
        self.values = self.format_list(self.get_res(self.get_candidates(self.flag)))
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
