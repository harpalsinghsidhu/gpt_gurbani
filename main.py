import os
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.uix.label import Label
from kivy.properties import NumericProperty, BooleanProperty, StringProperty
from kivy.uix.screenmanager import ScreenManager, Screen 
from kivy.core.text import LabelBase
from kivy.resources import resource_add_path
from database import PaathDatabase

KV = r"""
#:import dp kivy.metrics.dp
<ReaderScreen>:
    BoxLayout:
        orientation: "vertical"
        padding: dp(14)
        spacing: dp(10)
        canvas.before:
            Color:
                rgba: (0.97, 0.94, 0.86, 1)
            Rectangle:
                pos: self.pos
                size: self.size
        BoxLayout:
            size_hint_y: None
            height: dp(48)
            Label:
                text: "ਸ੍ਰੀ ਗੁਰੂ ਗ੍ਰੰਥ ਸਾਹਿਬ ਜੀ"
                font_name: "GurmukhiUni"
                color: (0.18, 0.14, 0.10, 1)
                font_size: "19sp"
            Button:
                text: "Sections"
                size_hint_x: None
                width: dp(92)
                on_release: app.root.current = "sections"
        Label:
            text: root.ang_label
            font_name: "GurmukhiUni"
            size_hint_y: None
            height: dp(28)
            color: (0.35, 0.28, 0.20, 1)
        ScrollView:
            id: scroll
            do_scroll_x: False
            bar_width: dp(5)
            BoxLayout:
                id: lines_box
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                padding: dp(10), dp(20)
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
            Button:
                text: "Ang -"
                on_release: root.change_ang(-1)
            Button:
                text: "Ang +"
                on_release: root.change_ang(1)
                
<SectionsScreen>:
    BoxLayout:
        orientation: "vertical"
        padding: dp(18)
        spacing: dp(12)
        Label:
            text: "ਬਾਣੀ ਦੇ ਭਾਗ"
            font_name: "GurmukhiUni"
            font_size: "24sp"
            size_hint_y: None
            height: dp(55)
        Button:
            text: "ਸ੍ਰੀ ਗੁਰੂ ਗ੍ਰੰਥ ਸਾਹਿਬ ਜੀ-Ang 1-1430"
            font_name: "GurmukhiUni"
            on_release: app.open_reader(1, 1430)
        Button:
            text: "ਜਪੁਜੀ ਸਾਹਿਬ"
            font_name: "GurmukhiUni"
            on_release: app.open_reader(1, 8)
        Button:
            text: "ਸੁਖਮਨੀ ਸਾਹਿਬ"
            font_name: "GurmukhiUni"
            on_release: app.open_reader(262, 296)
        Button:
            text: "ਰਾਗ ਅਨੁਸਾਰ ਬਾਣੀ"
            font_name: "GurmukhiUni"
            on_release: app.open_reader()
        Button:
            text: "Back to reader"
            on_release: app.root.current = "reader"
        Label:
            text: "Sections are navigation placeholders until verified scripture data is imported."
            text_size: self.width, None
            halign: "center"
            color: (0.4, 0.4, 0.4, 1)
"""

class ReaderScreen(Screen):
    running = BooleanProperty(True)
    speed = NumericProperty(30)
    display_text = StringProperty("")
    ang_label = StringProperty("Ang 1")
    ang = NumericProperty(1)
    min_ang = NumericProperty(1)
    max_ang = NumericProperty(1430)
    
    def on_enter(self):
        self.load_ang()
        self._event = Clock.schedule_interval(self.auto_scroll, 1 / 30)
        
    def on_leave(self):
        if hasattr(self, "_event"):
            self._event.cancel()
            
    def load_ang(self):
        app = App.get_running_app()
        text = app.db.get_ang(self.ang) or ""
        self.display_text = text
        self.ang_label = f"ਅੰਗ {self.ang} / {self.max_ang}"
        box = self.ids.lines_box
        box.clear_widgets()
        lines = [l for l in text.splitlines() if l.strip()] or [text]
        for i in range(0, len(lines), 4):
            lbl = Label(
                text="\n".join(lines[i:i + 4]),
                font_name="Gurmukhi",
                font_size=app.font_size,
                color=(0.12, 0.10, 0.08, 1),
                size_hint_y=None,
                halign="center",
                valign="top",
                text_size=(self.width - dp(40), None),
            )
            lbl.bind(width=lambda inst, w: setattr(inst, "text_size", (w - dp(20), None)))
            lbl.bind(texture_size=lambda inst, s: setattr(inst, "height", s[1] + dp(8)))
            box.add_widget(lbl)
        self.ids.scroll.scroll_y = 1
        
    def auto_scroll(self, dt):
        if self.running:
            # Speed controls the fraction of the scrollable area traversed per second.
            amount = (self.speed / 10000.0) * dt * 30
            self.ids.scroll.scroll_y = max(0, self.ids.scroll.scroll_y - amount)
            
    def set_speed(self, value):
        self.speed = value 
        
    def toggle_scroll(self):
        self.running = not self.running
        
    def to_top(self):
        self.ids.scroll.scroll_y = 1
        
    def change_ang(self, delta):
        self.ang = max(self.min_ang, min(self.max_ang, self.ang + delta))
        self.load_ang()
        
class SectionsScreen(Screen):
    pass 
    
class PaathReaderApp(App):
    font_size = "25sp"
    
    def build(self):
        self.title = "SGGS Paath Reader"
        self.db = PaathDatabase(readonly=True)
        base = os.path.dirname(os.path.abspath(__file__))
        LabelBase.register(name="Gurmukhi", fn_regular=os.path.join(base, "assets", "GurmukhiASCII.ttf"))
        LabelBase.register(name="GurmukhiUni", fn_regular=os.path.join(base, "assets", "Gurmukhi.ttf"))
        Builder.load_string(KV)
        manager = ScreenManager()
        manager.add_widget(ReaderScreen(name="reader"))
        manager.add_widget(SectionsScreen(name="sections"))
        return manager
        
    def open_reader(self, start=1, end=1430):
        reader = self.root.get_screen("reader")
        reader.min_ang = start
        reader.max_ang = end
        reader.ang = start
        self.root.current = "reader"
        
    def on_stop(self):
        self.db.close()
        
if __name__ == "__main__":
    PaathReaderApp().run()
