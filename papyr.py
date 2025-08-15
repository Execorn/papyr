#!/usr/bin/python
import sys
import os
import argparse
import gi

# We only import GTK if we are running the GUI
if "--run-daemon-loop" not in sys.argv:
    gi.require_version('Gtk', '4.0')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from papyr import daemon

def main():
    """The main entry point for the Papyr application."""
    parser = argparse.ArgumentParser(description="A rofi-inspired wallpaper selector.")
    parser.add_argument(
        "--slideshow",
        choices=["start", "stop"],
        help="Control the wallpaper slideshow daemon."
    )
    parser.add_argument(
        "--run-daemon-loop",
        action="store_true",
        help=argparse.SUPPRESS # Hide this internal argument from users
    )

    args = parser.parse_args()

    if args.run_daemon_loop:
        daemon.run_loop()
    elif args.slideshow == "start":
        daemon.start()
    elif args.slideshow == "stop":
        daemon.stop()
    else:
        # If no arguments are given, run the GUI
        from papyr.main import PapyrApplication
        app = PapyrApplication()
        sys.exit(app.run(sys.argv))

if __name__ == "__main__":
    main()