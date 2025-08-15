import os
import sys
import tomli

CONFIG_PATH = os.path.expanduser("~/.config/papyr/config.toml")
IGNORE_LIST_PATH = os.path.expanduser("~/.config/papyr/ignore.list")
ORDER_LIST_PATH = os.path.expanduser("~/.config/papyr/order.list")

class Config:
    """Manages Papyr's configuration."""

    def __init__(self, path: str = CONFIG_PATH):
        # Set default values
        self.wallpaper_dirs = []
        self.close_on_unfocus = True
        self.slideshow_interval = 10
        self.enable_pywal = False

        try:
            with open(path, "rb") as f:
                cfg = tomli.load(f)
                
                self.wallpaper_dirs = [os.path.expanduser(d) for d in cfg.get("wallpaper_dirs", [])]
                
                if 'behavior' in cfg and isinstance(cfg.get('behavior'), dict):
                    self.close_on_unfocus = cfg['behavior'].get('close_on_unfocus', self.close_on_unfocus)
                
                if 'slideshow' in cfg and isinstance(cfg.get('slideshow'), dict):
                    self.slideshow_interval = cfg['slideshow'].get('interval', self.slideshow_interval)

                # New: Load feature settings
                if 'features' in cfg and isinstance(cfg.get('features'), dict):
                    self.enable_pywal = cfg['features'].get('enable_pywal', self.enable_pywal)
        except FileNotFoundError:
            pass
        except tomli.TOMLDecodeError as e:
            print(f"Error parsing config {path}: {e}", file=sys.stderr)