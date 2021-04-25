import json
import logging
import re

import requests

from .parser.osis import parse_osis
from .translit import Hebrew
from .utils import get_cache_path


_BOOK_IDS = [
    "Gen", "Exod", "Lev", "Num", "Deut", "Josh", "Judg", "1Sam", "2Sam", "1Kgs", "2Kgs", 
    "Isa", "Jer", "Ezek", "Hos", "Joel", "Amos", "Obad", "Jonah", "Mic", "Nah", "Hab", "Zeph", "Hag", "Zech", "Mal",
    "Ps", "Prov", "Job", "Song", "Ruth", "Lam", "Eccl", "Esth", "Dan", "Ezra", "Neh", "1Chr", "2Chr",
]

_HEWLC_ROOT_URL = "https://raw.githubusercontent.com/openscriptures/morphhb/master/wlc"
_GRTISCH_URL = "https://raw.githubusercontent.com/morphgnt/tischendorf-data/master/OSIS-XML/2.8/tischendorfmorph.OSIS.xml"

_HEB = Hebrew()


def fetch_translation_from_openscriptures(translation):
    """
    Parse openscriptures xml-files and make my own json ones, then upload to dynamodb.
    """
    if translation == "hewlc":
        records = []
        for book_id in _BOOK_IDS:
            logging.info(f"Working on {book_id}")
            path = _download_hewlc(book_id)
            records.extend(parse_osis(path, w_tag_parser="hebrew"))
        logging.info("Performing transliteration")
        _transliterate(records)
    elif translation == "grtisch":
        path = _download_grtisch()
        records = parse_osis(path, w_tag_parser="greek")
    return records


def _download_hewlc(book_id):
    path = get_cache_path("raw", "hewlc", f"{book_id.lower()}_osis.xml")
    if not path.exists():
        url = f"{_HEWLC_ROOT_URL}/{book_id}.xml"
        logging.info(f"Requesting {url}")
        r = requests.get(url)
        with path.open("wb") as f:
            f.write(r.content)
    return path


def _download_grtisch():
    path = get_cache_path("raw", "grtisch", "grtisch_osis.xml")
    if not path.exists():
        url = _GRTISCH_URL
        logging.info(f"Requesting {url}")
        r = requests.get(url)
        with path.open("wb") as f:
            f.write(r.content)
    return path


def _transliterate(records):
    for record in records:
        tokens = record["tokens"]
        for token, next_token in zip(tokens, tokens[1:] + [{"type": "punc"}]):
            w = _HEB.strip_cantillations(token["text"])
            if next_token["type"] == "suf":
                w = w + next_token["text"]
            if token["type"] == "suf":
                token["tlit"] = ""
            else:
                token["tlit"] = _HEB.transliterate(w)
