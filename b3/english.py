import json
import logging
from pathlib import Path
import re
import sys

import requests

from .utils import get_cache_path, parse_xml


_ROOT_URL = "https://raw.githubusercontent.com/gratis-bible/bible/master/en"

# USFX and OSIS are common open standards, see diffs here: https://ebible.org/usfx/#differences
# This contains good stuff: https://ebible.org/Scriptures/engwebp_usfx.zip


def fetch_english(translation):
    """
    Fetch and parse openscriptures xml-files.
    """
    translation = translation.lower()
    logging.info(f"Downloading {translation}.xml")
    path = _download_file(translation)
    records = _parse_file(translation, path)
    logging.info(f"Parsed {len(records)} verses")
    return records


def _download_file(translation):
    path = get_cache_path("raw", translation, f"{translation}.xml")
    if not path.exists():
        url = f"{_ROOT_URL}/{translation}.xml"
        logging.info(f"Requesting {url}")
        r = requests.get(url)
        with path.open('wb') as f:
            f.write(r.content)
    return path


def _parse_file(translation, path):
    logging.info(f"Parsing {path}")
    tree = parse_xml(path)
    records = []
    prev_book = None
    for verse in tree.findall("*/div/chapter/verse"):
        book, c, v = verse.attrib["osisID"].split('.')
        records.append({
            "chapterId": f"{book}.{c}",
            "verseNum": int(v),
            "tokens": [
                {
                    "text": w,
                    "type": "w" if w.strip() else "s",
                }
                for w in re.split(r"(\s+)", verse.text.replace("`", "'").strip())
            ],
        })
        if book != prev_book:
            logging.info(f"Parsing {book}")
            prev_book = book
    return records
