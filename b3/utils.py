import logging
import warnings

from pathlib import Path
from urllib3.exceptions import InsecureRequestWarning

import requests


_CACHE_DIR = Path(__file__).parent.parent / ".cache"


def download(url, path):
    """
    Download file from internet.
    """
    if not path.exists():
        logging.info(f"Downloading {url}")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=InsecureRequestWarning)
            r = requests.get(url, verify=False)
        with path.open("wb") as f:
            f.write(r.content)


def get_cache_path(*args):
    """
    Get a specific cache path, and ensure the directory exists.
    """
    path = _CACHE_DIR
    for arg in args:
        path = path / arg
    path.parent.mkdir(parents=True, exist_ok=True)
    return path