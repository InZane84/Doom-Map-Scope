'''from importlib.metadata import version

try:
    __version__ = version("doom-map-scope")
except Exception:
    __version__ = "unknown"
    '''

import tomllib
from pathlib import Path

def get_version():
    pyproject_path = Path(__file__).parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)
    return data["project"]["version"]

__version__ = get_version()

def main():
    print("Hello from doom-map-scope!")


if __name__ == "__main__":
    main()
