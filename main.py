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
        self.current_flag = "g"
        self.current_item = 0
        self.query = ""
        self.values = self.format_list(self.get_res(self.get_candidates(self.current_flag)))
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
        return "\n".join(
            (
                "> " + value if i == self.current_item else "  " + value
            )
            for i, value in enumerate(self.values)
        )

    def update(self, app:Application):
        self.values = self.format_list(self.get_res(self.get_candidates(self.current_flag)))
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


    def on_input_buffer_change(buf:Buffer):
        searchList.query = buf.text
        searchList.update(app)

    buffer1.on_text_changed += on_input_buffer_change 

    app.run()

if __name__ == "__main__":
    main()
