"""
wadfile_cache.py

Module for caching downloaded WAD files from the idGames archive.
"""

import os
import io
from pathlib import Path

CACHE_DIR = Path("/tmp/doom_mapscope_cache")
MAX_CACHE_SIZE = 250*1024*1024
CACHE_DIR.mkdir(exist_ok=True)

def get_cache_path(wad_id):
    """Generate cache file path from WAD ID"""
    return CACHE_DIR / f"wad_{wad_id}.zip"

def get_cache_size():
    """Get total size of cached files in bytes"""
    if not CACHE_DIR.exists():
        return 0
    return sum(f.stat().st_size for f in CACHE_DIR.glob("wad_*.zip"))

def cleanup_cache(needed_space):
    """Remove oldest files if cache exceeds limit"""
    cache_size = get_cache_size()

    if cache_size + needed_space > MAX_CACHE_SIZE:
        print(f"Cache cleanup: {cache_size / 1024 / 1024:.1f}MB + {needed_space / 1024 / 1024:.1f}MB needed")

        # Get all cached files sorted by modification time (oldest first)
        cached_files = sorted(CACHE_DIR.glob("wad_*.zip"), key=lambda f: f.stat().st_mtime)

        # Delete oldest files until we have space
        for cache_file in cached_files:
            if cache_size + needed_space <= MAX_CACHE_SIZE:
                break
            file_size = cache_file.stat().st_size
            cache_file.unlink()
            cache_size -= file_size
            print(f"Deleted cache: {cache_file.name} ({file_size / 1024 / 1024:.1f}MB)")
# wadfile_downloader and extract_wad_from_zip are
# just hanging out here in the cache implementation for now
def wadfile_downloader(user_input):
    """Get a wadfile over http from the idGames database with caching"""
    wad_id = user_input.split("://")[-1].strip()
    cache_path = get_cache_path(wad_id)

    # Check if already cached
    if cache_path.exists():
        print(f"Loading from cache: {cache_path}")
        with open(cache_path, 'rb') as f:
            wad_data = extract_wad_from_zip(f.read())
            wadfile.open_wadfile(sender='foo', app_data=io.BytesIO(wad_data))
        return

    try:
        with httpx.Client(follow_redirects=True) as client:
            api_url = f"https://doomworld.com/idgames/api/api.php?action=get&id={wad_id}&out=json"
            print(f"Requesting: {api_url}")
            response = client.get(api_url)
            data = response.json()

            # Display WAD info
            display_wadfile_info(data)

            # Download wadfile
            if 'content' in data:
                file_path = data['content']['dir'].strip('/')
                file_name = data['content']['filename']
                download_url = f"https://gamers.org/pub/idgames/{file_path}/{file_name}"

                print(f"Downloading from: {download_url}")
                _headers = {"User-Agent": "Mozilla/5.0 (Doom Map Scope)"}
                r = client.get(download_url, headers=_headers)
                r.raise_for_status()

                # Check cache space before saving
                cleanup_cache(len(r.content))

                # Save to cache
                cache_path.write_bytes(r.content)
                print(f"Cached: {cache_path} ({len(r.content) / 1024 / 1024:.1f}MB)")

                # Extract and open WAD
                wad_data = extract_wad_from_zip(r.content)
                wadfile.open_wadfile(sender='foo', app_data=io.BytesIO(wad_data))
                print(f"Successfully loaded WAD")

    except httpx.ConnectError:
        dpg.set_value("status_text", "Error: Could not connect to idGames")
    except Exception as e:
        dpg.set_value("status_text", f"Error: {str(e)}")

def extract_wad_from_zip(zip_content):
    """Extract WAD file from zip archive"""
    with zipfile.ZipFile(io.BytesIO(zip_content)) as z:
        wads = [f for f in z.namelist() if f.lower().endswith('.wad')]
        if wads:
            return z.read(wads[0])
    return None

def clear_cache():
    """Manually clear all cached files"""
    for cache_file in CACHE_DIR.glob("wad_*.zip"):
        cache_file.unlink()
    print("Cache cleared")

"""
# First download - fetches from server
    wadfile_downloader("15156")

# Second 'download' - from cache
    wadfile_downloader("15156")

# cleanup
    clear_cache()

# Check cache size
    print(f"Cache size: {get_cache_size() / 1024 / 1024:.1f}MB")
"""