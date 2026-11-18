import os
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
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
                color: (0.18, 0.14, 0.10, 1)
                font_size: "21sp"
                bold: True
            Button:
                text: "Sections"
                size_hint_x: None
                width: dp(92)
                on_release: app.root.current = "sections"
        Label:
            text: root.ang_label
            size_hint_y: None
            height: dp(28)
            color: (0.35, 0.28, 0.20, 1)
        ScrollView:
            id: scroll
            do_scroll_x: False
            bar_width: dp(5)
            Label:
                id: scripture
                text: root.display_text
                font_name: "Gurmukhi"
                font_size: app.font_size
                color: (0.12, 0.10, 0.08, 1)
                size_hint_y: None
                height: self.texture_size[1] + dp(40)
                text_size: self.width - dp(20), None
                halign: "center"
                valign: "top"
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
            font_size: "24sp"
            bold: True
            size_hint_y: None
            height: dp(55)
        Button:
            text: "ਸ੍ਰੀ ਗੁਰੂ ਗ੍ਰੰਥ ਸਾਹਿਬ ਜੀ-Ang 1-1430"
            on_release: app.open_reader()
        Button:
            text: "ਜਪੁਜੀ ਸਾਹਿਬ"
            on_release: app.open_reader()
        Button:
            text: "ਸੁਖਮਨੀ ਸਾਹਿਬ"
            on_release: app.open_reader()
        Button:
            text: "ਰਾਗ ਅਨੁਸਾਰ ਬਾਣੀ"
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
    
    def on_enter(self):
        self.load_ang()
        self._event = Clock.schedule_interval(self.auto_scroll, 1 / 30)
        
    def on_leave(self):
        if hasattr(self, "_event"):
            self._event.cancel()
            
    def load_ang(self):
        app = App.get_running_app()
        self.display_text = app.db.get_ang(self.ang)
        self.ang_label = f"ਅੰਗ {self.ang} / 1430"
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
        self.ang = max(1, min(1430, self.ang + delta))
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
        
    def open_reader(self):
        self.root.current = "reader"
        
    def on_stop(self):
        self.db.close()
        
if __name__ == "__main__":
    PaathReaderApp().run()
