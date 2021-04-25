from pathlib import Path


_CACHE_DIR = Path(__file__).parent.parent / ".cache"


def get_cache_path(*args):
    """
    Get a specific cache path, and ensure the directory exists.
    """
    path = _CACHE_DIR
    for arg in args:
        path = path / arg
    path.parent.mkdir(parents=True, exist_ok=True)
    return path