import os
import sys
import tomli

CONFIG_PATH = os.path.expanduser("~/.config/papyr/config.toml")


class Config:
    """Manages Papyr's configuration."""

    def __init__(self, path: str = CONFIG_PATH):

        self.wallpaper_dirs = []
        self.close_on_unfocus = True

        try:
            with open(path, "rb") as f:

                cfg = tomli.load(f)
                print("--- RAW CONFIG PARSED ---")
                print(cfg)
                print("-------------------------")

                dirs = cfg.get("wallpaper_dirs", [])
                self.wallpaper_dirs = [os.path.expanduser(d) for d in dirs if isinstance(
                    d, str) and os.path.isdir(os.path.expanduser(d))]

                if 'behavior' in cfg and isinstance(cfg.get('behavior'), dict):
                    self.close_on_unfocus = cfg['behavior'].get(
                        'close_on_unfocus', True)

            print(
                f"FINAL LOADED SETTING: 'close_on_unfocus' is {self.close_on_unfocus}")

        except FileNotFoundError:
            print(
                f"FATAL: Configuration file not found at {path}. Please create it.", file=sys.stderr)
        except tomli.TOMLDecodeError as e:
            print(
                f"FATAL: Could not parse {path}. It may have a syntax error: {e}", file=sys.stderr)
