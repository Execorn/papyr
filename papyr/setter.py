import subprocess
import shutil

def set_wallpaper(file_path: str):
    """
    Sets the desktop wallpaper using the best available tool.
    Currently supports feh.
    """
    print(f"Attempting to set wallpaper: {file_path}")

    # 1. Check for 'feh'
    if shutil.which("feh"):
        try:
            subprocess.run(["feh", "--bg-fill", file_path], check=True)
            print("Successfully set wallpaper using feh.")
            return
        except subprocess.CalledProcessError as e:
            print(f"Feh command failed: {e}")
            return
    
    # You could add other setters like nitrogen or swaybg here in the future
    # if shutil.which("nitrogen"):
    #   ...
    
    print("Error: Could not find a wallpaper setting utility like 'feh'.")
    print("Please install feh to set wallpapers.")
