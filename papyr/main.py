import sys
import os
import gi
from gi.repository import  GLib
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk
from .window import PapyrWindow

class PapyrApplication(Gtk.Application):
    """The main application class for Papyr."""
    def __init__(self, **kwargs):
        super().__init__(application_id="com.execorn.papyr", **kwargs)

    def do_startup(self):
        """Called once when the application starts, before do_activate."""
        Gtk.Application.do_startup(self)
        self.load_css()

    def do_activate(self):
        """Called when the application is activated."""
        win = self.get_active_window()
        if not win:
            win = PapyrWindow(application=self)
        win.present()
        
    def load_css(self):
        """Loads the application's CSS file for styling."""
        css_provider = Gtk.CssProvider()
        style_file = os.path.join(os.path.dirname(__file__), 'style.css')
        try:
            css_provider.load_from_path(style_file)
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(), 
                css_provider, 
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
        except GLib.Error as e:
            print(f"Could not load CSS file {style_file}: {e}")