import os
import sys
import time
import signal
import random
import subprocess
import psutil
from .config import Config, IGNORE_LIST_PATH, ORDER_LIST_PATH
from .setter import set_wallpaper

PID_FILE = os.path.expanduser("~/.cache/papyr/daemon.pid")

def get_pid():
    """Reads the PID from the PID file, returns None if not found or invalid."""
    if not os.path.exists(PID_FILE):
        return None
    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        if psutil.pid_exists(pid):
            return pid
        else:
            # The process is gone, clean up the stale PID file
            os.remove(PID_FILE)
            return None
    except (ValueError, FileNotFoundError):
        return None

def start():
    """Starts the slideshow daemon in the background."""
    if get_pid():
        print("Slideshow daemon is already running.")
        return

    config = Config()
    
    # Launch this same script as a new detached process
    # with the argument '--run-daemon-loop'
    executable = sys.executable
    script_path = os.path.abspath(sys.argv[0])
    
    process = subprocess.Popen(
        [executable, script_path, "--run-daemon-loop"],
        start_new_session=True # This detaches it from our current terminal
    )

    with open(PID_FILE, 'w') as f:
        f.write(str(process.pid))

    print(f"Slideshow daemon started with interval of {config.slideshow_interval} minutes.")

def stop():
    """Stops the running slideshow daemon."""
    pid = get_pid()
    if not pid:
        print("Slideshow daemon is not running.")
        return

    try:
        process = psutil.Process(pid)
        process.terminate() # Ask it to shut down gracefully
        print("Slideshow daemon stopped.")
    except psutil.NoSuchProcess:
        print("Slideshow daemon was not running (stale PID file cleaned).")
    finally:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
            
def run_loop():
    """The main loop for the daemon process."""
    config = Config()
    
    try:
        with open(IGNORE_LIST_PATH, 'r') as f:
            ignore_list = set(line.strip() for line in f)
    except FileNotFoundError:
        ignore_list = set()

    # --- New: Order-aware wallpaper loading ---
    wallpaper_list = []
    use_random_shuffle = True
    
    if os.path.exists(ORDER_LIST_PATH):
        print("Daemon: Custom order list found. Using it.")
        with open(ORDER_LIST_PATH, 'r') as f:
            wallpaper_list = [line.strip() for line in f if line.strip() not in ignore_list]
        use_random_shuffle = False # Respect the user's order
    else:
        print("Daemon: No order list found. Scanning directories.")
        VALID_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp'}
        all_images = []
        for directory in config.wallpaper_dirs:
            for entry in os.scandir(directory):
                path = entry.path
                if entry.is_file() and os.path.splitext(path)[1].lower() in VALID_EXTENSIONS:
                    if path not in ignore_list:
                        all_images.append(path)
        wallpaper_list = all_images

    if not wallpaper_list:
        print("Daemon: No valid wallpapers found. Exiting.")
        return

    if use_random_shuffle:
        random.shuffle(wallpaper_list)

    interval_seconds = config.slideshow_interval * 60
    current_index = 0

    while True:
        if current_index >= len(wallpaper_list):
            current_index = 0
            if use_random_shuffle:
                random.shuffle(wallpaper_list)

        wallpaper = wallpaper_list[current_index]
        # We must also pass the config object here.
        set_wallpaper(wallpaper, config)
        current_index += 1
        
        time.sleep(interval_seconds)