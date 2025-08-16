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

# --- NEW: Global state variables for signal handlers ---
is_paused = False
force_next_wallpaper = False
# --- END NEW ---

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

# --- NEW: Signal handler functions ---
def handle_sig_pause_resume(signum, frame):
    """Toggles the pause state."""
    global is_paused
    is_paused = not is_paused
    if is_paused:
        print("Daemon: Paused.")
    else:
        print("Daemon: Resumed.")

def handle_sig_next(signum, frame):
    """Forces the next wallpaper to be set."""
    global force_next_wallpaper
    force_next_wallpaper = True
    print("Daemon: Skipping to next wallpaper.")

def handle_sig_prev(signum, frame):
    """Forces the previous wallpaper to be set."""
    # This signal handler needs to communicate back to the main loop.
    # We'll use a global flag similar to the 'next' handler.
    global force_prev_wallpaper
    force_prev_wallpaper = True
    print("Daemon: Skipping to previous wallpaper.")
# --- END NEW ---

def run_loop():
    """The main loop for the daemon process."""
    # --- NEW: Register signal handlers ---
    signal.signal(signal.SIGUSR1, handle_sig_pause_resume)
    signal.signal(signal.SIGUSR2, handle_sig_next)
    # Using SIGHUP for 'prev' as a distinct signal
    signal.signal(signal.SIGHUP, handle_sig_prev)
    global force_next_wallpaper
    global force_prev_wallpaper # Add this global
    force_prev_wallpaper = False
    # --- END NEW ---

    config = Config()
    
    try:
        with open(IGNORE_LIST_PATH, 'r') as f:
            ignore_list = set(line.strip() for line in f)
    except FileNotFoundError:
        ignore_list = set()

    wallpaper_list = []
    use_random_shuffle = True
    
    if os.path.exists(ORDER_LIST_PATH):
        print("Daemon: Custom order list found. Using it.")
        with open(ORDER_LIST_PATH, 'r') as f:
            wallpaper_list = [line.strip() for line in f if line.strip() not in ignore_list]
        use_random_shuffle = False
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
        # --- MODIFIED: Main loop logic for responsiveness ---
        while is_paused:
            time.sleep(1) # Wait efficiently while paused

        if force_prev_wallpaper:
            current_index -= 2 # Move back two positions
            if current_index < -1:
                current_index = len(wallpaper_list) - 2
            force_prev_wallpaper = False

        if current_index >= len(wallpaper_list):
            current_index = 0
            if use_random_shuffle:
                random.shuffle(wallpaper_list)
        
        if current_index < 0:
            current_index = len(wallpaper_list) -1


        wallpaper = wallpaper_list[current_index]
        set_wallpaper(wallpaper, config)
        current_index += 1
        
        # Wait for the interval, but check for signals every second
        for _ in range(interval_seconds):
            if force_next_wallpaper or force_prev_wallpaper or is_paused:
                break # Exit sleep loop immediately
            time.sleep(1)
        
        if force_next_wallpaper:
            force_next_wallpaper = False
            continue # Skip to the next iteration
        # --- END MODIFIED ---