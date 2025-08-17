import subprocess
import shutil
import os
import sys
import json
from .config import Config

def _run_pywal(file_path: str):
    """Helper function to run pywal if enabled and available."""
    if shutil.which("wal"):
        print("Pywal integration enabled. Generating new color scheme...")
        try:
            # Explicitly add the --backend wal to avoid issues with pywal-colors-rust,
            # which does not support --backend colorz
            subprocess.run(["wal", "-i", file_path, "-n", "--backend", "wal"], check=True)
            print("Pywal color scheme generated.")
        except subprocess.CalledProcessError as e:
            print(f"Pywal command failed: {e}")
    else:
        print("Warning: 'wal' command not found, skipping pywal integration.")

def detect_monitors() -> list[str]:
    """Detects connected monitors using swaymsg or xrandr."""
    # Wayland (Sway) check first
    if shutil.which("swaymsg"):
        try:
            result = subprocess.run(["swaymsg", "-t", "get_outputs", "-r"], check=True, capture_output=True, text=True)
            outputs = json.loads(result.stdout)
            return [output['name'] for output in outputs if output['active']]
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError) as e:
            print(f"Swaymsg monitor detection failed: {e}", file=sys.stderr)
            
    # X11 (xrandr) as fallback
    if shutil.which("xrandr"):
        try:
            result = subprocess.run(["xrandr", "--query"], check=True, capture_output=True, text=True)
            monitors = []
            for line in result.stdout.splitlines():
                if " connected" in line and not "disconnected" in line:
                    monitors.append(line.split()[0])
            return monitors
        except subprocess.CalledProcessError as e:
            print(f"Xrandr monitor detection failed: {e}", file=sys.stderr)
            
    return []


def set_wallpaper(file_path: str, config: Config, monitor: str | None = None):
    """Sets the desktop wallpaper, optionally for a specific monitor."""
    print(f"Attempting to set wallpaper: {file_path}")
    if monitor:
        print(f"Targeting monitor: {monitor}")
    
    setter = config.setter
    
    # Auto-detection logic
    if setter == "auto":
        # Prefer swaymsg if sway is running
        if os.environ.get("SWAYSOCK"):
             if shutil.which("swaymsg"):
                setter = "swaymsg"
             elif shutil.which("swaybg"):
                setter = "swaybg"
        elif os.environ.get("WAYLAND_DISPLAY"):
            # Placeholder for other Wayland compositors
            pass
        elif os.environ.get("XDG_CURRENT_DESKTOP"):
            desktop = os.environ.get("XDG_CURRENT_DESKTOP").lower()
            if "gnome" in desktop or "cinnamon" in desktop:
                setter = "gnome"
        
        # Fallback for X11 tiling WMs
        if setter == "auto" and shutil.which("feh"):
            setter = "feh"

    # --- Execute Setter Command ---
    setter_success = False
    try:
        if setter == "feh":
            if monitor:
                print("Warning: 'feh' setter does not support specific monitors. Applying to all.")
            if not shutil.which("feh"):
                print("Error: 'feh' command not found.")
                return
            subprocess.run(["feh", "--bg-fill", file_path], check=True)
            print("Successfully set wallpaper using feh.")
            setter_success = True

        elif setter == "swaybg":
            if monitor:
                print("Warning: 'swaybg' is not ideal for multi-monitor. Use 'swaymsg'. Applying to all outputs.")
            if not shutil.which("swaybg"):
                print("Error: 'swaybg' command not found.")
                return
            subprocess.run(["pkill", "swaybg"], check=False)
            subprocess.Popen(["swaybg", "-i", file_path, "-m", "fill"])
            print("Successfully set wallpaper using swaybg.")
            setter_success = True
            
        elif setter == "swaymsg":
            if not shutil.which("swaymsg"):
                print("Error: 'swaymsg' command not found.")
                return
            target_monitor = monitor if monitor else "*"
            cmd = f'output "{target_monitor}" bg "{os.path.abspath(file_path)}" fill'
            subprocess.run(["swaymsg", cmd], check=True)
            print(f"Successfully set wallpaper for {target_monitor} using swaymsg.")
            setter_success = True
            
        elif setter == "gnome":
            if monitor:
                print("Warning: 'gnome' setter does not support specific monitors. Applying to all.")
            picture_uri = f"file://{os.path.abspath(file_path)}"
            subprocess.run(["gsettings", "set", "org.gnome.desktop.background", "picture-uri", picture_uri], check=True)
            subprocess.run(["gsettings", "set", "org.gnome.desktop.background", "picture-uri-dark", picture_uri], check=True)
            print("Successfully set wallpaper using gsettings (GNOME).")
            setter_success = True

        else:
            print(f"Error: Unknown or unsupported setter '{setter}'. Please check your config.")
            return

    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Setter command '{setter}' failed: {e}")
        return

    # --- Run Pywal Integration Post-set ---
    if setter_success and config.enable_pywal:
        _run_pywal(file_path)