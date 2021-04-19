import json
import logging
from pathlib import Path
import re
import sys

import requests

from .utils import parse_xml


_CACHE_DIR = Path(__file__).parent.parent / ".cache" / "b3-en-raw"
_ROOT_URL = "https://raw.githubusercontent.com/gratis-bible/bible/master/en"

# USFX and OSIS are common open standards, see diffs here: https://ebible.org/usfx/#differences
# This contains good stuff: https://ebible.org/Scriptures/engwebp_usfx.zip


def fetch_english(translation, limit):
    """
    Parse openscriptures xml-files and make my own json ones, then upload to dynamodb.
    """
    translation = translation.lower()
    logging.info(f"Downloading {translation}.xml")
    _download_file(translation)
    records = _parse_file(translation, limit)
    logging.info(f"Parsed {len(records)} verses")
    return records


def _download_file(translation):
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = _CACHE_DIR / f"{translation}.xml"
    if not path.exists():
        url = f"{_ROOT_URL}/{translation}.xml"
        logging.info(f"Requesting {url}")
        r = requests.get(url)
        with path.open('wb') as f:
            f.write(r.content)


def _parse_file(translation, limit):
    path = _CACHE_DIR / f"{translation}.xml"
    logging.info(f"Parsing {path}")
    tree = parse_xml(path)
    records = []
    prev_book = None
    for verse in tree.findall("*/div/chapter/verse"):
        book, c, v = verse.attrib["osisID"].split('.')
        records.append({
            "chapterId": f"{translation.upper()}:{book}.{c}",
            "verseNum": int(v),
            "tokens": [
                {
                    "text": w,
                    "type": "word" if w.strip() else "space",
                }
                for w in re.split(r"(\s+)", verse.text.replace("`", "'").strip())
            ],
        })
        if book != prev_book:
            logging.info(f"Parsing {book}")
            prev_book = book
        if len(records) == limit:
            logging.warning(f"Reached limit of {limit} - stopping!")
            break
    return records
