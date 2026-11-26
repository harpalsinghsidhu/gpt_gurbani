import os
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import NumericProperty, BooleanProperty, StringProperty
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.stencilview import StencilView
from kivy.core.text import LabelBase
from kivy.utils import escape_markup
from database import PaathDatabase

# Scroll speed: slider value x this = pixels per second
PX_PER_SPEED = 1.2

GUR_DIGITS = str.maketrans("0123456789", "੦੧੨੩੪੫੬੭੮੯")


def gur_num(n):
    return str(n).translate(GUR_DIGITS)


def title_markup(gur, eng, extra=""):
    """Gurmukhi in the Unicode font, English in the normal font."""
    s = ""
    if gur:
        s += "[font=GurmukhiUni]" + escape_markup(gur) + "[/font]"
    if eng:
        s += ("   " if s else "") + "[size=14sp]" + escape_markup(eng) + "[/size]"
    if extra:
        s += "   [size=12sp]" + escape_markup(extra) + "[/size]"
    return s


class Teleprompter(StencilView):
    """Shows a whole section as one continuous scroll.

    Only 2-4 blocks of text exist at any time, so even the full SGGS
    (1430 Angs) uses very little memory and never makes a huge texture.
    Drag with a finger to move up/down by hand.
    """
    page_word = StringProperty("ਅੰਗ")

    def __init__(self, **kw):
        super().__init__(**kw)
        self.parts = []          # [(page, part, text), ...]
        self.items = []          # Label widgets currently alive
        self.first = 0           # index in parts of items[0]
        self.offset = 0.0        # pixels items[0] is scrolled above the top
        self.dragging = False
        self.at_end = False
        self._built_w = 0
        self.bind(size=self._on_geometry, pos=self._on_geometry)

    # ---- loading -------------------------------------------------------
    def load(self, parts):
        self._clear()
        self.parts = list(parts)
        self.first = 0
        self.offset = 0.0
        self.at_end = False
        self._fill()

    def to_top(self):
        self.load(self.parts)

    def _clear(self):
        for it in self.items:
            self.remove_widget(it)
        self.items = []

    def _on_geometry(self, *args):
        if self.parts and self.width > 0 and self.width != self._built_w:
            self._clear()
            self.offset = 0.0
            self.at_end = False
            self._fill()
        else:
            self._place()

    # ---- building one block -------------------------------------------
    def _make(self, idx):
        page, part, text = self.parts[idx]
        marker = ""
        if part == 0 and page:
            marker = ("[font=GurmukhiUni][size=16sp][color=#8a7a60]— "
                      + self.page_word + " " + gur_num(page)
                      + " —[/color][/size][/font]\n")
        lbl = Label(
            text=marker + escape_markup(text),
            markup=True,
            font_name="Gurmukhi",
            font_size="25sp",
            color=(0.12, 0.10, 0.08, 1),
            halign="center",
            valign="top",
            size_hint=(None, None),
        )
        lbl.text_size = (self.width - dp(24), None)
        lbl.texture_update()
        lbl.size = (self.width, lbl.texture_size[1] + dp(14))
        self._built_w = self.width
        return lbl

    def _total(self):
        return sum(i.height for i in self.items)

    # ---- keeping the right blocks alive ---------------------------------
    def _fill(self):
        if not self.parts or self.width <= 0:
            return
        h = self.height
        margin = dp(300)
        if not self.items:
            it = self._make(self.first)
            self.items.append(it)
            self.add_widget(it)
        # drop blocks that are completely above the top
        while len(self.items) > 1 and self.offset >= self.items[0].height:
            self.offset -= self.items[0].height
            self.remove_widget(self.items.pop(0))
            self.first += 1
        # scrolled back up: bring previous blocks in at the top
        while self.offset < 0 and self.first > 0:
            self.first -= 1
            it = self._make(self.first)
            self.items.insert(0, it)
            self.add_widget(it)
            self.offset += it.height
        if self.offset < 0:
            self.offset = 0.0
        # add blocks at the bottom until the screen is covered
        while (self.first + len(self.items) < len(self.parts)
               and self._total() - self.offset < h + margin):
            it = self._make(self.first + len(self.items))
            self.items.append(it)
            self.add_widget(it)
        # free blocks far below the screen
        while (len(self.items) > 2
               and self._total() - self.items[-1].height - self.offset > h + margin):
            self.remove_widget(self.items.pop())
        # stop at the very end
        is_last = self.first + len(self.items) >= len(self.parts)
        limit = max(0.0, self._total() - h)
        if is_last and self.offset > limit:
            self.offset = limit
        self.at_end = is_last and self.offset >= limit - 0.5
        self._place()

    def _place(self):
        y = self.top + self.offset
        for it in self.items:
            y -= it.height
            it.pos = (self.x, y)

    def advance(self, dy):
        """dy > 0 moves the text up (reading forward)."""
        self.offset += dy
        self._fill()

    def status(self):
        if not self.parts or not self.items:
            return ""
        page = self.parts[self.first][0]
        h0 = max(1.0, self.items[0].height)
        done = self.first + min(1.0, self.offset / h0)
        pct = int(100 * done / len(self.parts))
        return ("[font=GurmukhiUni]" + self.page_word + " " + gur_num(page)
                + "[/font]    " + str(pct) + "%")

    # ---- finger drag ----------------------------------------------------
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.grab(self)
            self.dragging = True
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            self.advance(touch.dy)
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            self.dragging = False
            return True
        return super().on_touch_up(touch)


class SectionRow(Button):
    section_id = StringProperty("")
    is_header = BooleanProperty(False)


KV = r"""
#:import dp kivy.metrics.dp

<SectionRow>:
    markup: True
    halign: "left"
    valign: "middle"
    text_size: self.width - dp(24), self.height
    background_normal: ""
    background_down: ""
    background_color: (0.42, 0.28, 0.10, 1) if self.is_header else (0.93, 0.88, 0.75, 1)
    color: (1, 0.95, 0.85, 1) if self.is_header else (0.15, 0.11, 0.07, 1)
    on_release: app.open_section(self.section_id) if not self.is_header else None

<ReaderScreen>:
    BoxLayout:
        orientation: "vertical"
        padding: dp(10)
        spacing: dp(8)
        canvas.before:
            Color:
                rgba: (0.97, 0.94, 0.86, 1)
            Rectangle:
                pos: self.pos
                size: self.size
        BoxLayout:
            size_hint_y: None
            height: dp(52)
            spacing: dp(8)
            Label:
                text: root.title_text
                markup: True
                color: (0.18, 0.14, 0.10, 1)
                font_size: "20sp"
                text_size: self.size
                halign: "center"
                valign: "middle"
            Button:
                text: "Sections"
                size_hint_x: None
                width: dp(92)
                on_release: app.root.current = "sections"
        Label:
            text: root.progress_text
            markup: True
            size_hint_y: None
            height: dp(26)
            color: (0.35, 0.28, 0.20, 1)
        Teleprompter:
            id: tele
        BoxLayout:
            size_hint_y: None
            height: dp(42)
            Label:
                text: "Speed"
                color: (0.2, 0.16, 0.12, 1)
                size_hint_x: None
                width: dp(55)
            Slider:
                id: speed
                min: 5
                max: 100
                value: 30
                on_value: root.set_speed(self.value)
            Label:
                text: str(int(speed.value))
                color: (0.2, 0.16, 0.12, 1)
                size_hint_x: None
                width: dp(34)
        BoxLayout:
            size_hint_y: None
            height: dp(48)
            spacing: dp(8)
            Button:
                text: "Pause" if root.running else "Resume"
                on_release: root.toggle_scroll()
            Button:
                text: "Top"
                on_release: root.to_top()

<SectionsScreen>:
    BoxLayout:
        orientation: "vertical"
        padding: dp(10)
        spacing: dp(8)
        canvas.before:
            Color:
                rgba: (0.97, 0.94, 0.86, 1)
            Rectangle:
                pos: self.pos
                size: self.size
        Label:
            text: "[font=GurmukhiUni]ਬਾਣੀ ਦੇ ਭਾਗ[/font]"
            markup: True
            font_size: "24sp"
            color: (0.18, 0.14, 0.10, 1)
            size_hint_y: None
            height: dp(52)
        RecycleView:
            id: rv
            viewclass: "SectionRow"
            do_scroll_x: False
            bar_width: dp(5)
            RecycleBoxLayout:
                default_size: None, dp(54)
                default_size_hint: 1, None
                size_hint_y: None
                height: self.minimum_height
                orientation: "vertical"
                spacing: dp(3)
"""


class ReaderScreen(Screen):
    running = BooleanProperty(True)
    speed = NumericProperty(30)
    title_text = StringProperty("")
    progress_text = StringProperty("")
    _event = None

    def open_section(self, section_id):
        app = App.get_running_app()
        info, parts = app.db.get_section(section_id)
        if info is None:
            return
        gur, eng, key = info
        self.title_text = title_markup(gur, eng)
        tele = self.ids.tele
        tele.page_word = "ਅੰਗ" if key == "sggs" else "ਪੰਨਾ"
        tele.load(parts)
        self.running = True
        self.progress_text = tele.status()

    def on_enter(self):
        self._stop_clock()
        self._event = Clock.schedule_interval(self.tick, 1 / 30)

    def on_leave(self):
        self._stop_clock()

    def _stop_clock(self):
        if self._event is not None:
            self._event.cancel()
            self._event = None

    def tick(self, dt):
        tele = self.ids.tele
        if self.running and not tele.dragging:
            tele.advance(self.speed * PX_PER_SPEED * dt)
            if tele.at_end:
                self.running = False
        self.progress_text = tele.status()

    def set_speed(self, value):
        self.speed = value

    def toggle_scroll(self):
        self.running = not self.running

    def to_top(self):
        self.ids.tele.to_top()
        self.running = True


class SectionsScreen(Screen):
    def load_sections(self):
        app = App.get_running_app()
        data = []
        last_group = None
        for gid, gg, ge, sid, sg, se, key, a, b in app.db.list_sections():
            if gid != last_group:
                data.append({"text": title_markup(gg, ge),
                             "section_id": "", "is_header": True})
                last_group = gid
            unit = "Ang" if key == "sggs" else "Page"
            rng = f"{unit} {a}-{b}" if a != b else f"{unit} {a}"
            data.append({"text": title_markup(sg, se, rng),
                         "section_id": sid, "is_header": False})
        self.ids.rv.data = data


class PaathReaderApp(App):
    def build(self):
        self.title = "Paath Reader"
        self.db = PaathDatabase(readonly=True)
        base = os.path.dirname(os.path.abspath(__file__))
        LabelBase.register(name="Gurmukhi",
                           fn_regular=os.path.join(base, "assets", "GurmukhiASCII.ttf"))
        LabelBase.register(name="GurmukhiUni",
                           fn_regular=os.path.join(base, "assets", "Gurmukhi.ttf"))
        Builder.load_string(KV)
        manager = ScreenManager()
        sections = SectionsScreen(name="sections")
        manager.add_widget(sections)
        manager.add_widget(ReaderScreen(name="reader"))
        sections.load_sections()
        return manager

    def open_section(self, section_id):
        self.root.get_screen("reader").open_section(section_id)
        self.root.current = "reader"

    def on_stop(self):
        self.db.close()


if __name__ == "__main__":
    PaathReaderApp().run()
