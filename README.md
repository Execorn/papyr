# Papyr
A fast, lightweight, and `rofi`-inspired wallpaper manager for Linux desktops. Papyr provides a visual, keyboard-driven interface to instantly select, set, and organize your wallpapers, with powerful features like a slideshow daemon and automatic terminal theming.

It is designed for users of tiling window managers (`awesome`, `i3`, `bspwm`, etc.) but now includes support for Wayland compositors and full desktop environments like GNOME.

![MVP Interface](mvp.png)

## Features
- **Fluid Thumbnail Grid:** Displays a beautiful, gapless grid of wallpaper previews using `Gtk.FlowBox`.
- **Real-time Filtering:** Instantly filter wallpapers by filename using a `rofi`-style search bar.
- **Full-Screen Preview:** Press `Spacebar` on a selected image to view it in full-screen before setting.
- **Efficient Caching:** Thumbnails are generated once and cached in `~/.cache/papyr/`, ensuring near-instant startups.
- **Advanced Slideshow Daemon:** Run a background process to cycle through your wallpapers. Pause, resume, and skip tracks from the command line—perfect for binding to media keys.
- **Multi-Backend Support:** Works out-of-the-box on different environments by supporting `feh` (X11), `swaybg` (Wayland), and `gsettings` (GNOME/Cinnamon), with an automatic detection mode.
- **Multi-Monitor Aware:** Detects multiple monitors and allows setting wallpapers on specific screens via the right-click context menu (requires a compatible backend like `swaymsg`).
- **Ignore List:** Hide wallpapers from the main view without deleting the files (`Delete` key).
- **Customizable Order:** Organize your wallpapers with keyboard shortcuts (`Ctrl+J`/`K`) or drag-and-drop. The slideshow respects this order.
- **`pywal` Integration:** Automatically generate a new terminal color scheme from the selected wallpaper.
- **Full Keyboard Control:** Navigate with arrow keys, select with `Enter`, ignore with `Delete`, preview with `Spacebar`, reorder with `Ctrl+J`/`K`, and toggle the ignore view with `Ctrl+I`.
- **Customizable Theming:** The look and feel can be easily customized using a simple CSS stylesheet.

## Installation & Dependencies

Papyr is a Python application that uses GTK4.

#### 1. System Dependencies (Arch Linux)
Open a terminal and install the core dependencies using `pacman`:

```bash
sudo pacman -S python gtk4 python-gobject python-pip feh
```
- `feh` is used as a fallback setter. Other setters for your environment (like `swaybg` or `swaymsg` on Sway) may also be required.

#### 2. Python Dependencies
Install the required Python libraries using `pip`. `psutil` is used for safely managing the slideshow daemon.

```bash
pip install tomli Pillow psutil
```

#### 3. Get the Code
Clone this repository to your local machine:

```bash
git clone https://github.com/execorn/papyr.git
cd papyr
```

## Configuration

You must create a configuration file to tell Papyr where your wallpapers are located.

#### 1. Create the Config File

```bash
mkdir -p ~/.config/papyr
touch ~/.config/papyr/config.toml
```

#### 2. Edit the Config File
Paste the following into **`~/.config/papyr/config.toml`** and adjust it to your needs.

```toml
# A list of directories where Papyr should look for wallpapers.
# Use absolute paths or the ~ shortcut.
wallpaper_dirs = [
    "/home/execorn/wallpapers/imgs",
    "~/Pictures/Favorites"
]

[behavior]
# Set this to false if Papyr closes when you move the mouse away
# (common if your window manager uses "focus follows mouse").
# The value MUST be lowercase: true or false.
close_on_unfocus = false

[slideshow]
# The time between wallpaper changes, in minutes.
interval = 10

[features]
# Set to true to automatically run 'wal' after setting a new wallpaper.
# Requires 'wal' (pywal) to be in your PATH.
enable_pywal = true

[setter]
# Options: "auto", "feh", "swaybg", "swaymsg", "gnome".
# "auto" is recommended. It will try to detect your environment.
command = "auto"
```
Upon first use, Papyr will also create an `ignore.list` and `order.list` in this directory to persist your settings.

## Usage

#### Running the GUI
To select a wallpaper, simply run the main script. It's recommended to bind this command to a hotkey in your window manager.

```bash
python3 /path/to/papyr/papyr.py
```

#### Controlling the Slideshow
The slideshow is controlled via command-line arguments.

```bash
# Start the background daemon
python3 papyr.py --slideshow start

# Stop the background daemon
python3 papyr.py --slideshow stop

# Pause or resume the slideshow timer
python3 papyr.py --slideshow pause
python3 papyr.py --slideshow resume

# Immediately skip to the next or previous wallpaper
python3 papyr.py --slideshow next
python3 papyr.py --slideshow prev
```

#### In-App Hotkeys
- **`Enter` / `Double-Click`**: Set selected wallpaper and close.
- **`Spacebar`**: Show a full-screen preview of the selected wallpaper.
- **`Esc`**: Close without setting.
- **`Tab` / `Shift+Tab`**: Switch focus between the Search Bar and the wallpaper grid.
- **`Arrow Keys`**: Navigate the grid (when it has focus).
- **`Delete`**: Move the selected wallpaper to the ignore list.
- **`Ctrl+I`**: Toggle between the main view and the ignored wallpapers view.
- **`Ctrl+J` / `Ctrl+K`**: Move the selected wallpaper down or up in the order.

## Development Journey & Problems Encountered
-   **GTK4 Event Handling:** A significant challenge was architecting the keyboard event system. Early attempts with a single, central controller led to a cascade of unpredictable bugs where focus would be lost, the search bar would stop accepting text, or scrolling would fail after certain actions. The final, stable architecture uses a much simpler model where focus is explicitly passed between the search bar and the wallpaper grid (`Tab` key), allowing each widget to handle its own input (typing, arrow key navigation) without interference.
-   **Concurrency and Race Conditions:** Many UI bugs, such as scrolling jumping to the top of the list after reordering an item, were traced to race conditions. The fixes required using `GLib.idle_add` to defer UI updates like grabbing focus or scrolling until after GTK had finished its current processing and drawing cycle, ensuring the UI was in a stable state.
-   **`GtkPopoverMenu` Stability:** The right-click context menu would intermittently crash the application. This was traced to a memory management error where the menu was parented to a temporary widget (`GtkFlowBoxChild`) that could be destroyed. The solution was to parent the menu to the main application window itself, ensuring its stability.

## Future Development (TODO)
- [ ] **Custom Script Integration:** Add a `post_set_script` option to run custom commands after a wallpaper is set.
- [ ] **Wallpaper History:** Implement a view (`Ctrl+H`) to show recently used wallpapers.
- [ ] **Animated Drag-and-Drop:** Revisit `Gtk.DragSource` to implement smoother drag-and-drop animations.
- [ ] **Packaging:** Create a `setup.py` and a `PKGBUILD` for easier installation.