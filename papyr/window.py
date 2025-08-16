import sys
import os
import threading
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, GLib, GObject, Gio, GdkPixbuf
from .config import Config, IGNORE_LIST_PATH, ORDER_LIST_PATH
from . import thumbnailer
from . import setter

VALID_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp'}

class PapyrWindow(Gtk.ApplicationWindow):
    """The main window for the Papyr application."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self._setup_actions()
        self.config = Config()
        self.load_persistent_lists()
        self.all_discovered_paths = self.discover_images()
        self.is_showing_ignored = False
        self.dragged_child = None

        self.set_default_size(1000, 700)
        self.set_title("Papyr")
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_focusable(True)

        try:
            self.set_property("always-on-top", True)
        except Exception as e:
            print(f"Warning: Could not set 'always-on-top': {e}", file=sys.stderr)
            
        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        # --- MODIFIED: Center search entry and add CSS class ---
        self.search_entry = Gtk.SearchEntry(
            hexpand=False, 
            halign=Gtk.Align.CENTER, 
            margin_bottom=5, 
            margin_top=5,
        )
        self.search_entry.add_css_class("search-entry")
        # --- END MODIFIED ---
        self.search_entry.connect("search-changed", self.on_search_changed)
        main_vbox.append(self.search_entry)

        self.flowbox = Gtk.FlowBox()
        self.flowbox.set_valign(Gtk.Align.START)
        self.flowbox.set_max_children_per_line(5)
        self.flowbox.set_min_children_per_line(3)
        self.flowbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        
        scrolled_window = Gtk.ScrolledWindow(child=self.flowbox)
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_vexpand(True)
        main_vbox.append(scrolled_window)

        self.set_child(main_vbox)

        self.flowbox.connect("child-activated", self.on_child_activated)
        
        click_controller = Gtk.GestureClick.new()
        click_controller.set_button(Gdk.BUTTON_SECONDARY)
        click_controller.connect("pressed", self.on_right_click)
        self.flowbox.add_controller(click_controller)
        
        key_controller = Gtk.EventControllerKey.new()
        key_controller.connect("key-pressed", self.on_key_pressed)
        self.add_controller(key_controller)
        
        self.connect("map", self.on_map)

        self.start_thumbnail_loading()

    def _setup_actions(self):
        """Defines Gio.SimpleActions for the application window."""
        action_toggle_ignore = Gio.SimpleAction.new("toggle_ignore", None)
        action_toggle_ignore.connect("activate", lambda a, v: self._toggle_selected_item_ignore_status())
        self.add_action(action_toggle_ignore)
        
        action_reorder_up = Gio.SimpleAction.new("reorder_up", None)
        action_reorder_up.connect("activate", lambda a, v: self._reorder_selected_item(-1))
        self.add_action(action_reorder_up)
        
        action_reorder_down = Gio.SimpleAction.new("reorder_down", None)
        action_reorder_down.connect("activate", lambda a, v: self._reorder_selected_item(1))
        self.add_action(action_reorder_down)

    def load_persistent_lists(self):
        """Loads ignore and order lists from config files."""
        try:
            with open(IGNORE_LIST_PATH, 'r') as f:
                self.ignore_list = set(line.strip() for line in f)
        except FileNotFoundError:
            self.ignore_list = set()
        
        try:
            with open(ORDER_LIST_PATH, 'r') as f:
                self.order_list = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            self.order_list = []

    def discover_images(self) -> list[str]:
        """Discovers all images and merges with the saved order."""
        ordered_set = set(self.order_list)
        found_images = set()
        for directory in self.config.wallpaper_dirs:
            try:
                for entry in os.scandir(directory):
                    if entry.is_file() and os.path.splitext(entry.name)[1].lower() in VALID_EXTENSIONS:
                        found_images.add(entry.path)
            except OSError as e:
                print(f"Error scanning directory {directory}: {e}", file=sys.stderr)
        
        final_list = [path for path in self.order_list if path in found_images]
        new_images = sorted(list(found_images - ordered_set))
        final_list.extend(new_images)
        return final_list

    def start_thumbnail_loading(self):
        """Reloads the view based on the current display mode."""
        self.flowbox.remove_all()
        
        paths_to_show = []
        if self.is_showing_ignored:
            self.set_title("Papyr (Ignored Wallpapers)")
            paths_to_show = [p for p in self.all_discovered_paths if p in self.ignore_list]
        else:
            self.set_title("Papyr")
            paths_to_show = [p for p in self.all_discovered_paths if p not in self.ignore_list]

        thread = threading.Thread(target=self._thumbnail_loader_thread, args=(paths_to_show,), daemon=True)
        thread.start()

    def _thumbnail_loader_thread(self, paths_to_load):
        """Worker thread that generates thumbnails."""
        for path in paths_to_load:
            pixbuf = thumbnailer.get_pixbuf_for_image(path)
            if pixbuf:
                GLib.idle_add(self.add_wallpaper_to_flowbox, pixbuf, path)

    def add_wallpaper_to_flowbox(self, pixbuf, path):
        """Creates a widget for a wallpaper and adds it to the FlowBox."""
        picture = Gtk.Picture()
        picture.set_pixbuf(pixbuf)
        picture.set_can_shrink(False)
        
        child = Gtk.FlowBoxChild(child=picture)
        child.path = path

        if path in self.ignore_list:
            child.get_child().add_css_class("ignored-item")
            
        if not self.is_showing_ignored:
            self._setup_reordering_gesture(child)

        self.flowbox.insert(child, -1)
    
    def save_list_to_file(self, file_path, item_list):
        """Utility to save a list/set of strings to a file."""
        try:
            with open(file_path, 'w') as f:
                f.write('\n'.join(item_list) + '\n')
        except IOError as e:
            print(f"Error writing to {file_path}: {e}", file=sys.stderr)
            
    def on_child_activated(self, flowbox, child):
        """Sets the selected wallpaper and closes."""
        if child and hasattr(child, 'path'):
            setter.set_wallpaper(child.path, self.config)
            self.close()

    def on_key_pressed(self, controller, keyval, keycode, state):
        """Handles global key presses."""
        is_ctrl = state & Gdk.ModifierType.CONTROL_MASK
        
        if keyval == Gdk.KEY_Escape:
            self.close()
            return True

        if is_ctrl:
            if keyval == Gdk.KEY_i:
                self.is_showing_ignored = not self.is_showing_ignored
                self.start_thumbnail_loading()
                return True
            elif keyval == Gdk.KEY_j:
                self._reorder_selected_item(1)
                return True
            elif keyval == Gdk.KEY_k:
                self._reorder_selected_item(-1)
                return True
        elif keyval == Gdk.KEY_Delete:
            self._toggle_selected_item_ignore_status()
            return True
        elif keyval == Gdk.KEY_space:
            self._show_fullscreen_preview()
            return True

        is_search_focused = self.search_entry.has_focus()
        if not is_ctrl and not is_search_focused:
            char_unicode = Gdk.keyval_to_unicode(keyval)
            if char_unicode and chr(char_unicode).isprintable():
                self.search_entry.grab_focus()
                return False

        return False
            
    def on_right_click(self, gesture, n_press, x, y):
        """Shows a context menu for the clicked item."""
        child = self.flowbox.get_child_at_pos(x, y)
        if not child: return

        self.flowbox.select_child(child)
        is_ignored = child.path in self.ignore_list

        menu = Gio.Menu.new()
        menu.append("Un-ignore" if is_ignored else "Ignore", "win.toggle_ignore")
        if not self.is_showing_ignored:
            menu.append_section(None, Gio.Menu.new())
            menu.append("Move Up (Ctrl+K)", "win.reorder_up")
            menu.append("Move Down (Ctrl+J)", "win.reorder_down")
        
        popover = Gtk.PopoverMenu(menu_model=menu)
        popover.set_parent(child)
        popover.popup()
        
    def _toggle_selected_item_ignore_status(self):
        """Ignores or un-ignores the currently selected wallpaper."""
        selected = self.flowbox.get_selected_children()
        if not selected: return
        
        child = selected[0]
        path = child.path

        if path in self.ignore_list:
            self.ignore_list.remove(path)
        else:
            self.ignore_list.add(path)
        
        self.save_list_to_file(IGNORE_LIST_PATH, self.ignore_list)
        self.start_thumbnail_loading()

    def _reorder_selected_item(self, direction: int):
        """Moves the selected item up (-1) or down (+1) and saves the new order."""
        if self.is_showing_ignored: return
        
        selected = self.flowbox.get_selected_children()
        if not selected: return
        
        child = selected[0]
        current_pos = child.get_index()
        new_pos = max(0, current_pos + direction)
        
        self.flowbox.remove(child)
        self.flowbox.insert(child, new_pos)
        self.flowbox.select_child(child)
        
        # --- BUG FIX: Grab focus to re-enable arrow keys ---
        self.flowbox.grab_focus()
        # --- END FIX ---

        new_order = [c.path for c in self.flowbox]
        self.save_list_to_file(ORDER_LIST_PATH, new_order)
            
    def on_search_changed(self, search_entry):
        """Callback to filter the flowbox based on search query."""
        query = search_entry.get_text().lower()
        
        def filter_func(child):
            if not query:
                return True
            filename = os.path.basename(child.path)
            return query in filename.lower()

        self.flowbox.set_filter_func(filter_func)
        self.flowbox.invalidate_filter()

    def _show_fullscreen_preview(self):
        """Opens a new borderless window to preview the selected image."""
        selected = self.flowbox.get_selected_children()
        if not selected: return
        
        path = selected[0].path
        preview_window = Gtk.Window(transient_for=self, modal=True, decorated=False)
        
        picture = Gtk.Picture.new_for_filename(path)
        picture.set_content_fit(Gtk.ContentFit.CONTAIN)
        preview_window.set_child(picture)

        click_controller = Gtk.GestureClick.new()
        click_controller.connect("pressed", lambda *args: preview_window.close())
        preview_window.add_controller(click_controller)
        
        key_controller = Gtk.EventControllerKey.new()
        key_controller.connect("key-pressed", lambda *args: preview_window.close())
        preview_window.add_controller(key_controller)
        
        preview_window.fullscreen()
        preview_window.present()
    
    def on_map(self, widget):
        self.grab_focus()
        if self.config.close_on_unfocus:
            self.connect("notify::has-focus", self.on_focus_changed)

    def on_focus_changed(self, widget, gparam):
        GLib.timeout_add(100, self.check_focus_and_close)

    def check_focus_and_close(self):
        if not self.has_focus() and not self.search_entry.has_focus():
            self.close()
        return GLib.SOURCE_REMOVE

    def _setup_reordering_gesture(self, widget):
        """Applies a drag gesture for reordering to a widget."""
        gesture = Gtk.GestureDrag.new()
        gesture.connect("drag-begin", self._on_reorder_drag_begin, widget)
        gesture.connect("drag-end", self._on_reorder_drag_end)
        widget.add_controller(gesture)

    def _on_reorder_drag_begin(self, gesture, x, y, child_widget):
        """Called when the user starts dragging a wallpaper."""
        self.flowbox.select_child(child_widget)
        child_widget.set_opacity(0.5)
        self.dragged_child = child_widget

    def _on_reorder_drag_end(self, gesture, offset_x, offset_y):
        """Called when the user releases the mouse after dragging."""
        if not self.dragged_child:
            return

        self.dragged_child.set_opacity(1.0)
        
        start_pos = self.dragged_child.get_allocation()
        end_x = start_pos.x + offset_x + (start_pos.width / 2)
        end_y = start_pos.y + offset_y + (start_pos.height / 2)
        
        target_child = self.flowbox.get_child_at_pos(end_x, end_y)

        if target_child and target_child != self.dragged_child:
            target_pos = target_child.get_index()
            child_to_move = self.dragged_child
            
            self.flowbox.remove(child_to_move)
            self.flowbox.insert(child_to_move, target_pos)

            self.flowbox.select_child(child_to_move)
            
            new_order = [c.path for c in self.flowbox]
            self.save_list_to_file(ORDER_LIST_PATH, new_order)
            
        self.dragged_child = None