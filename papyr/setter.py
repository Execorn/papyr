import subprocess
import shutil
import os
from .config import Config

def _run_pywal(file_path: str):
    """Helper function to run pywal if enabled and available."""
    if shutil.which("wal"):
        print("Pywal integration enabled. Generating new color scheme...")
        try:
            subprocess.run(["wal", "-i", file_path, "-n", "--backend", "wal"], check=True)
            print("Pywal color scheme generated.")
        except subprocess.CalledProcessError as e:
            print(f"Pywal command failed: {e}")
    else:
        print("Warning: 'wal' command not found, skipping pywal integration.")


def set_wallpaper(file_path: str, config: Config):
    """Sets the desktop wallpaper using the configured setter and optionally runs pywal."""
    print(f"Attempting to set wallpaper: {file_path}")
    
    setter = config.setter
    
    # Auto-detection logic
    if setter == "auto":
        if os.environ.get("SWAYSOCK") or os.environ.get("WAYLAND_DISPLAY"):
            if shutil.which("swaybg"):
                setter = "swaybg"
            # Add other wayland setters here (hyprpaper, etc)
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
            if not shutil.which("feh"):
                print("Error: 'feh' command not found.")
                return
            subprocess.run(["feh", "--bg-fill", file_path], check=True)
            print("Successfully set wallpaper using feh.")
            setter_success = True

        elif setter == "swaybg":
            if not shutil.which("swaybg"):
                print("Error: 'swaybg' command not found.")
                return
            # swaybg needs a running process, so we start it and kill the old one
            subprocess.run(["pkill", "swaybg"], check=False) # Ignore error if no process exists
            subprocess.Popen(["swaybg", "-i", file_path, "-m", "fill"])
            print("Successfully set wallpaper using swaybg.")
            setter_success = True
            
        elif setter == "gnome":
            # Set for both light and dark mode to be safe
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