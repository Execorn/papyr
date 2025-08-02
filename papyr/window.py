from . import setter
from . import thumbnailer
from .config import Config
from gi.repository import Gtk, Gdk, GLib, GObject, Gio, GdkPixbuf
import sys
import os
import threading
import gi
gi.require_version('Gtk', '4.0')

VALID_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp'}


class PapyrWindow(Gtk.ApplicationWindow):
    """The main window for the Papyr application."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.config = Config()
        self.image_paths = self.discover_images()

        self.set_default_size(1000, 700)
        self.set_title("Papyr")
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_focusable(True)

        try:
            self.set_property("always-on-top", True)
        except Exception as e:
            print(
                f"Warning: Could not set 'always-on-top': {e}", file=sys.stderr)

        self.flowbox = Gtk.FlowBox()
        self.flowbox.set_valign(Gtk.Align.START)
        self.flowbox.set_max_children_per_line(5)
        self.flowbox.set_min_children_per_line(3)
        self.flowbox.set_selection_mode(Gtk.SelectionMode.SINGLE)

        self.flowbox.connect("child-activated", self.on_child_activated)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_child(self.flowbox)
        scrolled_window.set_policy(
            Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.set_child(scrolled_window)

        self.connect("map", self.on_map)
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self.on_key_pressed)
        self.add_controller(key_controller)

        self.start_thumbnail_loading()

    def add_wallpaper_to_flowbox(self, pixbuf, path):
        """Creates a widget and adds it to the FlowBox."""
        picture = Gtk.Picture()
        picture.set_pixbuf(pixbuf)
        picture.set_can_shrink(False)

        child = Gtk.FlowBoxChild()
        child.set_child(picture)

        child.path = path

        self.flowbox.insert(child, -1)

    def on_child_activated(self, flowbox, child):
        """Called when a wallpaper is selected (double-clicked or Enter)."""
        if child and hasattr(child, 'path'):
            print(f"Wallpaper selected: {child.path}")
            setter.set_wallpaper(child.path)
            self.close()

    def start_thumbnail_loading(self):
        thread = threading.Thread(
            target=self._thumbnail_loader_thread, daemon=True)
        thread.start()

    def _thumbnail_loader_thread(self):
        for path in self.image_paths:
            pixbuf = thumbnailer.get_pixbuf_for_image(path)
            if pixbuf:
                GLib.idle_add(self.add_wallpaper_to_flowbox, pixbuf, path)

    def discover_images(self) -> list[str]:
        found_images = []
        for directory in self.config.wallpaper_dirs:
            try:
                for entry in os.scandir(directory):
                    if entry.is_file():
                        file_extension = os.path.splitext(entry.name)[
                            1].lower()
                        if file_extension in VALID_EXTENSIONS:
                            found_images.append(entry.path)
            except OSError as e:
                print(
                    f"Error scanning directory {directory}: {e}", file=sys.stderr)
        return sorted(found_images)

    def on_map(self, widget):
        self.grab_focus()
        if self.config.close_on_unfocus:
            self.connect("notify::has-focus", self.on_focus_changed)

    def on_key_pressed(self, controller, keyval, keycode, state):
        if keyval == Gdk.KEY_Escape:
            self.close()

    def on_focus_changed(self, widget, gparam):
        GLib.timeout_add(100, self.check_focus_and_close)

    def check_focus_and_close(self):
        if not self.has_focus():
            self.close()
        return GLib.SOURCE_REMOVE
