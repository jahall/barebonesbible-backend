from pathlib import Path
import re
import xml.etree.ElementTree as ET


_CACHE_DIR = Path(__file__).parent.parent / ".cache"


def parse_xml(path):
    """
    Parse OSIS XML.
    """
    with path.open("r") as f:
        xmlstring = re.sub(r" xmlns=['\"][^'\"]+['\"]", "", f.read(), count=1)
    return ET.fromstring(xmlstring)


def get_cache_path(*args):
    """
    Get a specific cache path, and ensure the directory exists.
    """
    path = _CACHE_DIR
    for arg in args:
        path = path / arg
    path.parent.mkdir(parents=True, exist_ok=True)
    return path