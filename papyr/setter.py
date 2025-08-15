import subprocess
import shutil
from .config import Config

def set_wallpaper(file_path: str, config: Config):
    """Sets the desktop wallpaper and optionally runs pywal."""
    print(f"Attempting to set wallpaper: {file_path}")

    if shutil.which("feh"):
        try:
            subprocess.run(["feh", "--bg-fill", file_path], check=True)
            print("Successfully set wallpaper using feh.")
            
            # --- THE FIX ---
            # We must use the 'config' object (lowercase 'c') that was passed
            # into this function, not the 'Config' class (uppercase 'C').
            if config.enable_pywal and shutil.which("wal"):
            # --- END FIX ---
                print("Pywal integration enabled. Generating new color scheme...")
                try:
                    subprocess.run(["wal", "-i", file_path, "-n"], check=True)
                    print("Pywal color scheme generated.")
                except subprocess.CalledProcessError as e:
                    print(f"Pywal command failed: {e}")
            return
        except subprocess.CalledProcessError as e:
            print(f"Feh command failed: {e}")
            return
    
    print("Error: Could not find 'feh'. Please install it to set wallpapers.")