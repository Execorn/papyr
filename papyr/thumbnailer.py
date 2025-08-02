from gi.repository import GdkPixbuf, GLib
import os
import hashlib
from PIL import Image
import gi
gi.require_version('Gtk', '4.0')


Image.MAX_IMAGE_PIXELS = None


CACHE_DIR = os.path.expanduser("~/.cache/papyr/thumbnails")
THUMBNAIL_SIZE = (300, 300)

os.makedirs(CACHE_DIR, exist_ok=True)


def get_thumbnail_path(image_path: str) -> str:
    """Generates a unique, safe filename for the cached thumbnail."""
    hasher = hashlib.md5(image_path.encode('utf-8'))
    return os.path.join(CACHE_DIR, f"{hasher.hexdigest()}.png")


def create_thumbnail(original_path: str, cache_path: str):
    """Creates a thumbnail from the original image and saves it to the cache atomically."""
    temp_path = f"{cache_path}.tmp"
    try:
        with Image.open(original_path) as img:
            img.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
            img.save(temp_path, "PNG")
        os.rename(temp_path, cache_path)
    except Exception as e:
        print(f"Error creating thumbnail for {original_path}: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)


def get_pixbuf_for_image(image_path: str) -> GdkPixbuf.Pixbuf:
    """Gets a thumbnail, checking the cache first and handling corrupt files."""
    cache_path = get_thumbnail_path(image_path)

    try:
        original_mtime = os.path.getmtime(image_path)
        cache_mtime = os.path.getmtime(
            cache_path) if os.path.exists(cache_path) else 0
        if original_mtime > cache_mtime:
            create_thumbnail(image_path, cache_path)
    except FileNotFoundError:
        if not os.path.exists(cache_path):
            create_thumbnail(image_path, cache_path)

    if not os.path.exists(cache_path):
        return None

    try:
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(cache_path)
        return pixbuf
    except GLib.Error:
        print(
            f"CRITICAL: Caught corrupt cache file for {image_path}. Deleting.")
        os.remove(cache_path)
        return None
