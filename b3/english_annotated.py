import json
import logging
from pathlib import Path
import re
import sys
import zipfile

import requests

from .parser.usfx import parse_usfx
from .utils import get_cache_path


_TRANSLATION_FILE_MAP = {
    "asv": "eng-asv_usfx",  # American Standard Version
    "kjv": "eng-kjv2006_usfx",  # King James Version
    "web": "eng-web_usfx",  # World English Bible
    "wmb": "engwmb_usfx",  # World Messianic Bible
}
_ROOT_URL = "https://ebible.org/Scriptures"

# USFX and OSIS are common open standards, see diffs here: https://ebible.org/usfx/#differences
# This contains good stuff: https://ebible.org/Scriptures/engwebp_usfx.zip


def fetch_english_annotated(translation):
    """
    Fetch and parse USFX xml-files from ebible.org.
    """
    translation = translation.lower()
    filename = _TRANSLATION_FILE_MAP[translation]
    logging.info(f"Downloading {filename}.xml")
    path = _download_file(translation, filename)
    records = parse_usfx(path)
    logging.info(f"Parsed {len(records)} verses")
    return records


def _download_file(translation, filename):
    zippath = get_cache_path("raw", translation, f"{filename}.zip")
    if not zippath.exists():
        url = f"{_ROOT_URL}/{filename}.zip"
        logging.info(f"Requesting {url}")
        r = requests.get(url)
        with zippath.open("wb") as f:
            f.write(r.content)
    xmlpath = get_cache_path("raw", translation, f"{filename}.xml")
    if not xmlpath.exists():
        logging.info(f"Unpacking {xmlpath.name}")
        with zipfile.ZipFile(zippath) as z:
            with z.open(xmlpath.name) as xf, xmlpath.open("wb") as f:
                f.write(xf.read())
    return xmlpath