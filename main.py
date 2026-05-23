from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.key_bindings import key_binding
from rapidfuzz import process
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit import Application
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.buffer import Buffer
import sys
from prompt_toolkit import HTML, choice, print_formatted_text, prompt
from modules.games.bottles import get_bottle_games
from prompt_toolkit.widgets import RadioList


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

class SearchList:
    def __init__(self) -> None:
        self.current_flag = "g"
        self.query = ""
        self.values = self.format_list(self.get_res(self.get_candidates(self.current_flag)))
        self.control = FormattedTextControl(self.get_list_text)
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
        return "\n".join(self.values)

    def update(self, app:Application):
        self.values = self.format_list(self.get_res(self.get_candidates(self.current_flag)))
        app.invalidate()

kb = KeyBindings()

@kb.add('c-q')
def exit_(event):
        event.app.exit()

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
