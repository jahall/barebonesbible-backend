import json
import logging
from pathlib import Path
import re
import sys

import requests

from .oshb import parse_oshb_xml
from .translit import Hebrew


_BOOK_IDS = [
    'Gen', 'Exod', 'Lev', 'Num', 'Deut', 'Josh', 'Judg', '1Sam', '2Sam', '1Kgs', '2Kgs', 
    'Isa', 'Jer', 'Ezek', 'Hos', 'Joel', 'Amos', 'Obad', 'Jonah', 'Mic', 'Nah', 'Hab', 'Zeph', 'Hag', 'Zech', 'Mal',
    'Ps', 'Prov', 'Job', 'Song', 'Ruth', 'Lam', 'Eccl', 'Esth', 'Dan', 'Ezra', 'Neh', '1Chr', '2Chr',
]
_CACHE_DIR = Path(__file__).parent.parent / ".cache" / "b3-heb-raw"
_ROOT_URL = "https://raw.githubusercontent.com/openscriptures/morphhb/master/wlc"
_HEB = Hebrew()


def fetch_hebrew(limit):
    """
    Parse openscriptures xml-files and make my own json ones, then upload to dynamodb.
    """
    records = []
    for book_id in _BOOK_IDS:
        logging.info(f"Working on {book_id}")
        _download_file(book_id)
        records.extend(_parse_file(book_id))
        if len(records) >= limit:
            logging.warning(f"Reached limit of {limit} - stopping!")
            records = records[:limit]
            break
    for record in records:
        tokens = record["tokens"]
        for token, next_token in zip(tokens, tokens[1:] + [{"type": "space"}]):
            w = _HEB.strip_cantillations(token["text"])
            token["text_no_cantillations"] = w
            if next_token["type"] == "suffix":
                w = w + next_token["text"]
            if token["type"] == "suffix":
                token["transliteration"] = ""
            else:
                token["transliteration"] = _HEB.transliterate(w) 
    return records


def _download_file(book_id):
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = _CACHE_DIR / f"{book_id}.xml"
    if not path.exists():
        url = f"{_ROOT_URL}/{book_id}.xml"
        logging.info(f"Requesting {url}")
        r = requests.get(url)
        with path.open('wb') as f:
            f.write(r.content)


def _parse_file(book_id):
    path = _CACHE_DIR / f"{book_id}.xml"
    return parse_oshb_xml(path)
