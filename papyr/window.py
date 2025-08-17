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
        
        print("--- DEBUG: Initializing PapyrWindow ---")
        self.config = Config()
        self.monitors = setter.detect_monitors()
        print(f"DEBUG __init__: Detected monitors: {self.monitors}")

        self._setup_actions()
        self.load_persistent_lists()
        self.all_discovered_paths = self.discover_images()
        self.is_showing_ignored = False

        self.set_default_size(1000, 700)
        self.set_title("Papyr")
        self.set_decorated(False)
        self.set_resizable(False)

        try:
            self.set_property("always-on-top", True)
        except Exception:
            print("DEBUG __init__: WM does not support 'always-on-top'.")
            pass
            
        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self.search_entry = Gtk.SearchEntry(
            hexpand=False, halign=Gtk.Align.CENTER, 
            margin_top=5, margin_bottom=5,
        )
        self.search_entry.add_css_class("search-entry")
        self.search_entry.connect("search-changed", self.on_search_changed)
        main_vbox.append(self.search_entry)

        self.flowbox = Gtk.FlowBox()
        self.flowbox.set_valign(Gtk.Align.START)
        self.flowbox.set_max_children_per_line(5)
        self.flowbox.set_min_children_per_line(3)
        self.flowbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.flowbox.set_focusable(True)
        
        self.flowbox.connect("selected-children-changed", self.on_selection_changed)
        
        self.scrolled_window = Gtk.ScrolledWindow(child=self.flowbox)
        self.scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scrolled_window.set_vexpand(True)
        main_vbox.append(self.scrolled_window)

        self.set_child(main_vbox)

        self.flowbox.connect("child-activated", self.on_child_activated)
        
        key_controller = Gtk.EventControllerKey.new()
        key_controller.connect("key-pressed", self.on_key_pressed)
        self.add_controller(key_controller)
        
        click_controller = Gtk.GestureClick.new()
        click_controller.set_button(Gdk.BUTTON_SECONDARY)
        click_controller.connect("pressed", self.on_right_click)
        self.flowbox.add_controller(click_controller)
        
        self.connect("map", self.on_map)
        print("DEBUG __init__: Widget setup complete.")
        self.start_thumbnail_loading()

    def _setup_actions(self):
        print("DEBUG _setup_actions: Setting up Gio.SimpleActions.")
        action_close = Gio.SimpleAction.new("close", None)
        action_close.connect("activate", lambda a, v: self.close())
        self.add_action(action_close)
        
        action_toggle = Gio.SimpleAction.new("toggle_ignore", None)
        action_toggle.connect("activate", lambda a, v: self._toggle_selected_item_ignore_status())
        self.add_action(action_toggle)

        action_reorder_up = Gio.SimpleAction.new("reorder_up", None)
        action_reorder_up.connect("activate", lambda a,v: self._reorder_selected_item(-1))
        self.add_action(action_reorder_up)
        
        action_reorder_down = Gio.SimpleAction.new("reorder_down", None)
        action_reorder_down.connect("activate", lambda a,v: self._reorder_selected_item(1))
        self.add_action(action_reorder_down)

        set_monitor_action = Gio.SimpleAction.new("set_for_monitor", GLib.VariantType.new('s'))
        set_monitor_action.connect("activate", self._on_set_for_monitor)
        self.add_action(set_monitor_action)

    def load_persistent_lists(self):
        print("DEBUG: Loading ignore and order lists.")
        try:
            with open(IGNORE_LIST_PATH, 'r') as f: self.ignore_list = set(line.strip() for line in f)
        except FileNotFoundError: self.ignore_list = set()
        try:
            with open(ORDER_LIST_PATH, 'r') as f: self.order_list = [line.strip() for line in f if line.strip()]
        except FileNotFoundError: self.order_list = []

    def discover_images(self) -> list[str]:
        print("DEBUG: Discovering images.")
        ordered_set, found_images = set(self.order_list), set()
        for directory in self.config.wallpaper_dirs:
            try:
                for entry in os.scandir(directory):
                    if entry.is_file() and os.path.splitext(entry.name)[1].lower() in VALID_EXTENSIONS:
                        found_images.add(entry.path)
            except OSError as e: print(f"ERROR: Cannot scan {directory}: {e}", file=sys.stderr)
        final_list = [path for path in self.order_list if path in found_images]
        final_list.extend(sorted(list(found_images - ordered_set)))
        print(f"DEBUG: Found {len(final_list)} images.")
        return final_list

    def start_thumbnail_loading(self):
        print("DEBUG: Starting background thumbnail loading.")
        self.flowbox.remove_all()
        paths = [p for p in self.all_discovered_paths if (p in self.ignore_list if self.is_showing_ignored else p not in self.ignore_list)]
        self.set_title(f"Papyr{' (Ignored)' if self.is_showing_ignored else ''}")
        threading.Thread(target=self._thumbnail_loader_thread, args=(paths,), daemon=True).start()

    def _thumbnail_loader_thread(self, paths):
        for path in paths:
            if pixbuf := thumbnailer.get_pixbuf_for_image(path):
                GLib.idle_add(self.add_wallpaper_to_flowbox, pixbuf, path)

    def add_wallpaper_to_flowbox(self, pixbuf, path):
        # --- PERMANENT FIX FOR 'pixbuf' PROPERTY CRASH ---
        picture = Gtk.Picture()
        picture.set_pixbuf(pixbuf)
        picture.set_can_shrink(False)
        # --- END FIX ---
        
        child = Gtk.FlowBoxChild(child=picture)
        # --- PERMANENT FIX FOR SETTING CUSTOM ATTRIBUTE ---
        child.path = path
        # --- END FIX ---

        self.flowbox.insert(child, -1)
        if child.get_index() == 0:
            print("DEBUG: First item added. Deferring selection until map.")
    
    def on_key_pressed(self, controller, keyval, keycode, state):
        key_name = Gdk.keyval_name(keyval)
        is_ctrl = bool(state & Gdk.ModifierType.CONTROL_MASK)
        focused = self.get_focus()
        print(f"DEBUG on_key_pressed: Key='{key_name}', Ctrl={is_ctrl}, focused='{type(focused).__name__}'")

        if keyval == Gdk.KEY_Escape:
            print("DEBUG on_key_pressed: Escape pressed, closing.")
            self.close()
            return True
        
        if self.search_entry.has_focus():
             print("DEBUG on_key_pressed: Search has focus, letting it handle key.")
             return False # Let the search entry process the key press

        if is_ctrl:
            if keyval == Gdk.KEY_i: self._toggle_ignore_view(); return True
            if keyval == Gdk.KEY_j: self._reorder_selected_item(1); return True
            if keyval == Gdk.KEY_k: self._reorder_selected_item(-1); return True
        elif keyval == Gdk.KEY_Delete: self._toggle_selected_item_ignore_status(); return True
        elif keyval == Gdk.KEY_space: self._show_fullscreen_preview(); return True

        return False

    def on_right_click(self, gesture, n_press, x, y):
        child = self.flowbox.get_child_at_pos(x, y)
        if not child: return
        print(f"DEBUG on_right_click: Menu for '{os.path.basename(child.path)}'")
        self.flowbox.select_child(child)
        menu = self._build_context_menu(child.path in self.ignore_list)
        
        # This two-step process with attachment to the toplevel window is crash-proof
        popover = Gtk.PopoverMenu(menu_model=menu)
        popover.set_parent(self) 
        popover.set_pointing_to(child.get_allocation())
        popover.popup()

    def _build_context_menu(self, is_ignored):
        print("DEBUG: Building context menu.")
        menu = Gio.Menu.new()
        if self.monitors:
            submenu = Gio.Menu.new()
            # The 'all' target is a special case
            item_all = Gio.MenuItem.new("All Monitors", 'win.set_for_monitor')
            item_all.set_action_and_target_value('win.set_for_monitor', GLib.Variant('s', 'all'))
            submenu.append_item(item_all)
            
            for m in self.monitors:
                item_m = Gio.MenuItem.new(f"Only on {m}", 'win.set_for_monitor')
                item_m.set_action_and_target_value('win.set_for_monitor', GLib.Variant('s', m))
                submenu.append_item(item_m)
                
            menu.append_submenu("Set Wallpaper", submenu)
            menu.append_section(None, Gio.Menu.new())
        
        menu.append("Un-ignore" if is_ignored else "Ignore", "win.toggle_ignore")
        if not self.is_showing_ignored:
            menu.append_section(None, Gio.Menu.new())
            menu.append("Move Up (Ctrl+K)", "win.reorder_up")
            menu.append("Move Down (Ctrl+J)", "win.reorder_down")
        return menu

    def _reorder_selected_item(self, direction):
        if not (selected := self.flowbox.get_selected_children()): return
        child = selected[0]
        pos, new_pos = child.get_index(), max(0, child.get_index() + direction)
        print(f"DEBUG reorder: Moving '{os.path.basename(child.path)}' from {pos} to {new_pos}")
        
        self.flowbox.remove(child)
        self.flowbox.insert(child, new_pos)
        self.flowbox.select_child(child)
        
        order = [c.path for c in self.flowbox]
        self.save_list_to_file(ORDER_LIST_PATH, order)

    def on_selection_changed(self, flowbox):
        if not (selected := flowbox.get_selected_children()): return
        print(f"DEBUG on_selection_changed: Scheduling scroll for '{os.path.basename(selected[0].path)}'.")
        GLib.idle_add(self._scroll_to_child, selected[0])

    def _scroll_to_child(self, child):
        alloc = child.get_allocation()
        # Wait until the widget is properly allocated
        if alloc.width == 0: return GLib.SOURCE_REMOVE
        
        vadj = self.scrolled_window.get_vadjustment()
        upper, page = vadj.get_value(), vadj.get_page_size()
        
        if alloc.y < upper:
            new_val = alloc.y
            print(f"DEBUG scroll: Child above view. Scrolling UP to {new_val}.")
            vadj.set_value(new_val)
        elif alloc.y + alloc.height > upper + page:
            new_val = max(0, alloc.y + alloc.height - page)
            print(f"DEBUG scroll: Child below view. Scrolling DOWN to {new_val}.")
            vadj.set_value(new_val)
        
        child.grab_focus()
        print(f"DEBUG scroll: Focus grabbed by '{os.path.basename(child.path)}'")
        return GLib.SOURCE_REMOVE

    def on_map(self, widget):
        print("DEBUG on_map: Window mapped. Focusing search entry and selecting first item.")
        self.search_entry.grab_focus()
        if child := self.flowbox.get_child_at_index(0):
            self.flowbox.select_child(child)
        
        if self.config.close_on_unfocus:
            self.connect("notify::has-focus", self.on_focus_changed)
    
    def on_focus_changed(self, widget, gparam):
        # A small delay helps prevent closing when focus shifts momentarily between widgets
        GLib.timeout_add(250, self.check_focus_and_close)
    
    def check_focus_and_close(self):
        focus = self.get_focus()
        has_focus = focus is not None
        print(f"DEBUG check_focus: Window has_focus={self.has_focus()}, focused widget='{type(focus).__name__}'")
        if not self.has_focus():
            print("DEBUG check_focus: Window reports no focus. Closing.")
            self.close()
        return GLib.SOURCE_REMOVE # Prevents the timer from running repeatedly

    def on_child_activated(self, flowbox, child):
        setter.set_wallpaper(child.path, self.config)
        self.close()

    def on_search_changed(self, search_entry):
        query = search_entry.get_text().lower()
        print(f"DEBUG on_search_changed: Filtering with '{query}'")
        self.flowbox.set_filter_func(lambda c: not query or query in os.path.basename(c.path).lower())
        self.flowbox.invalidate_filter()

    def _toggle_ignore_view(self):
        print("DEBUG: Toggling ignore view.")
        self.is_showing_ignored = not self.is_showing_ignored
        self.start_thumbnail_loading()

    def _toggle_selected_item_ignore_status(self):
        if not (selected := self.flowbox.get_selected_children()): return
        path = selected[0].path
        print(f"DEBUG: Toggling ignore for '{os.path.basename(path)}'")
        if path in self.ignore_list: self.ignore_list.remove(path)
        else: self.ignore_list.add(path)
        self.save_list_to_file(IGNORE_LIST_PATH, self.ignore_list)
        self.start_thumbnail_loading()

    def save_list_to_file(self, file_path, item_list):
        print(f"DEBUG: Saving {len(item_list)} items to {file_path}")
        try:
            with open(file_path, 'w') as f: f.write('\n'.join(item_list) + '\n')
        except IOError as e: print(f"ERROR: Could not save to {file_path}: {e}", file=sys.stderr)
    
    def _show_fullscreen_preview(self):
        if not (selected := self.flowbox.get_selected_children()): return
        path = selected[0].path
        print(f"DEBUG: Previewing '{os.path.basename(path)}'")
        
        win = Gtk.Window(transient_for=self, decorated=False, modal=True)
        # --- PERMANENT FIX FOR `filename` PROPERTY CRASH ---
        picture = Gtk.Picture.new_for_filename(path)
        picture.set_content_fit(Gtk.ContentFit.CONTAIN)
        win.set_child(picture)
        # --- END FIX ---
        
        for event in ["pressed", "key-pressed"]:
            ctl = Gtk.GestureClick.new() if event == "pressed" else Gtk.EventControllerKey.new()
            ctl.connect(event, lambda *a: win.close())
            win.add_controller(ctl)
            
        win.fullscreen()
        win.present()
    
    def _setup_reordering_gesture(self, widget):
        # Drag and drop is disabled for stability.
        pass

    def _on_set_for_monitor(self, action, parameter):
        if not (selected := self.flowbox.get_selected_children()): return
        monitor = parameter.get_string()
        print(f"DEBUG: Setting wallpaper for monitor: {monitor}")
        setter.set_wallpaper(selected[0].path, self.config, monitor if monitor != "all" else None)
        self.close()