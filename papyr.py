#!/usr/bin/python
import sys
import os
import argparse
import signal
import gi
from papyr import daemon

# We only import GTK if we are not running in a daemon context
if "--run-daemon-loop" not in sys.argv and "--slideshow" not in sys.argv:
    gi.require_version('Gtk', '4.0')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# --- NEW: Helper function to send signals ---
def send_daemon_signal(sig):
    """Sends a signal to the running daemon process."""
    pid = daemon.get_pid()
    if not pid:
        print("Error: Slideshow daemon is not running.")
        return
    try:
        os.kill(pid, sig)
        print("Signal sent to daemon.")
    except ProcessLookupError:
        print("Error: Daemon process not found (stale PID).")
    except Exception as e:
        print(f"An error occurred: {e}")
# --- END NEW ---

def main():
    """The main entry point for the Papyr application."""
    parser = argparse.ArgumentParser(description="A rofi-inspired wallpaper selector.")
    parser.add_argument(
        "--slideshow",
        # --- MODIFIED: Added new choices ---
        choices=["start", "stop", "pause", "resume", "next", "prev"],
        # --- END MODIFIED ---
        help="Control the wallpaper slideshow daemon."
    )
    parser.add_argument(
        "--run-daemon-loop",
        action="store_true",
        help=argparse.SUPPRESS # Hide this internal argument from users
    )

    args = parser.parse_args()

    # --- MODIFIED: Handle new arguments ---
    if args.run_daemon_loop:
        daemon.run_loop()
    elif args.slideshow == "start":
        daemon.start()
    elif args.slideshow == "stop":
        daemon.stop()
    elif args.slideshow in ["pause", "resume"]:
        # SIGUSR1 is used to toggle the pause state in the daemon
        send_daemon_signal(signal.SIGUSR1)
    elif args.slideshow == "next":
        send_daemon_signal(signal.SIGUSR2)
    elif args.slideshow == "prev":
        # SIGHUP is used for 'prev' to have a distinct signal
        send_daemon_signal(signal.SIGHUP)
    # --- END MODIFIED ---
    else:
        # If no arguments are given, run the GUI
        from papyr.main import PapyrApplication
        app = PapyrApplication()
        sys.exit(app.run(sys.argv))

if __name__ == "__main__":
    main()