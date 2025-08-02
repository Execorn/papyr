# Papyr
A fast, lightweight, and `rofi`-inspired wallpaper selector for Linux desktops, designed for users of tiling window managers like `awesome`, `i3`, or `bspwm`.

![MVP Interface](mvp.png)

## About Papyr
Papyr was born from the need for a quick, visual, and keyboard-driven way to manage and set wallpapers without the overhead of a full GUI application. It is designed to be launched with a hotkey, display a beautiful grid of your favorite wallpapers, and get out of your way.

The core philosophy is to be fast, simple, and highly configurable, integrating seamlessly into minimalist desktop environments.

## Features
- **Rofi-style Interface:** Launches a single, centered window on command. Closes on `Esc` or (optionally) when it loses focus.
- **Fluid Thumbnail Grid:** Uses a `FlowBox` layout to display a beautiful, gapless grid of wallpaper previews that adapts to different image sizes.
- **Efficient Caching:** Thumbnails are generated once and cached in `~/.cache/papyr/`, ensuring near-instant startups on subsequent runs.
- **Multi-Directory Support:** Scans multiple wallpaper directories you specify in its configuration.
- **Wallpaper Setter Integration:** Automatically detects and uses `feh` to set the selected wallpaper.
- **Keyboard & Mouse Driven:** Navigate with arrow keys, select with `Enter` or a double-click.
- **Customizable Theming:** The look and feel can be easily customized using a simple CSS stylesheet.

## Installation & Dependencies

Papyr is a Python application that uses GTK4. You will need to install the required system and Python packages.

#### 1. System Dependencies (Arch Linux)
Open a terminal and install the core dependencies using `pacman`:
```bash
sudo pacman -S python gtk4 python-gobject python-pip feh
```
- `python`: The Python 3 interpreter.
- `gtk4`: The underlying GUI toolkit.
- `python-gobject`: The Python bindings that allow our code to talk to GTK.
- `python-pip`: The standard Python package installer.
- `feh`: The backend utility used to set the wallpaper.

#### 2. Python Dependencies
Install the required Python libraries using `pip`:
```bash
pip install tomli Pillow
```
- `tomli`: A fast library for parsing `.toml` configuration files.
- `Pillow`: A powerful library for image manipulation (used for creating thumbnails).

#### 3. Get the Code
Clone this repository to your local machine:
```bash
git clone https://github.com/execorn/papyr.git
cd papyr
```

#### 4. Run Papyr
You can run the application directly from the project directory:
```bash
python3 papyr.py
```

## Configuration

Papyr will not run without a configuration file. You must tell it where to find your wallpapers.

#### 1. Create the Config File
Create the configuration directory and file:
```bash
mkdir -p ~/.config/papyr
touch ~/.config/papyr/config.toml
```

#### 2. Edit the Config File
Paste the following into your **`~/.config/papyr/config.toml`** and **edit the paths to match your system**.

```toml
# A list of directories where Papyr should look for wallpapers.
# Use absolute paths starting with /home/your_user or use ~.
wallpaper_dirs = [
    "/home/execorn/wallpapers/imgs",
    "/home/execorn/Pictures/more-wallpapers"
]

# This section controls application behavior.
[behavior]
# Set this to false if Papyr closes when you just move the mouse away.
# This is common if your window manager uses "focus follows mouse".
# The value MUST be lowercase: true or false.
close_on_unfocus = false
```

#### 3. Window Manager Integration (Optional but Recommended)
To make Papyr appear centered like `rofi`, you should add a rule to your window manager's configuration.

For **AwesomeWM**, add this to your `rc.lua` file in the `awful.rules.rules` section:
```lua
{ rule_any = { class = { "papyr" } },
  properties = { floating = true, placement = awful.placement.centered } },
```

## Customization
You can change the appearance of the grid by editing **`papyr/papyr/style.css`**. Feel free to adjust colors, spacing, and sizes.

```css
/* Style the child container of the FlowBox */
flowboxchild {
    padding: 6px;
    border-radius: 8px;
}

flowboxchild:selected {
    background-color: rgba(53, 132, 228, 0.4);
}
```

## Future Development (TODO)
Papyr is under active development. Planned features include:
- [ ] **Slideshow Mode:** A background daemon to automatically cycle through wallpapers at a set interval.
- [ ] **Ignore List:** Ability to right-click or press `Delete` on a wallpaper to hide it from view without deleting the file.
- [ ] **Reordering:** A mode to drag-and-drop or use keybindings to reorder the wallpaper list for the slideshow.
- [ ] **`pywal` Integration:** Automatically generate a new terminal color scheme from the selected wallpaper.
- [ ] **More Setters:** Add support for other wallpaper utilities like `nitrogen` (for X11) and `swaybg` (for Wayland).
- [ ] **Online Sources:** Add the ability to pull wallpapers from sources like Unsplash or wallhaven.cc.

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.