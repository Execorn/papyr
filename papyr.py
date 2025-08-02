
from papyr.main import PapyrApplication
import sys
import os
import gi

gi.require_version('Gtk', '4.0')


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


if __name__ == "__main__":
    app = PapyrApplication()
    sys.exit(app.run(sys.argv))
