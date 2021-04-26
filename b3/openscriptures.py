import json
import logging
import re

import requests

from .parser.osis import parse_osis
from .translit.greek import transliterate_greek
from .translit.hebrew import transliterate_hebrew
from .utils import download, get_cache_path


_BOOK_IDS = [
    "Gen", "Exod", "Lev", "Num", "Deut", "Josh", "Judg", "1Sam", "2Sam", "1Kgs", "2Kgs", 
    "Isa", "Jer", "Ezek", "Hos", "Joel", "Amos", "Obad", "Jonah", "Mic", "Nah", "Hab", "Zeph", "Hag", "Zech", "Mal",
    "Ps", "Prov", "Job", "Song", "Ruth", "Lam", "Eccl", "Esth", "Dan", "Ezra", "Neh", "1Chr", "2Chr",
]

_HEWLC_ROOT_URL = "https://raw.githubusercontent.com/openscriptures/morphhb/master/wlc"
_GRTISCH_URL = "https://raw.githubusercontent.com/morphgnt/tischendorf-data/master/OSIS-XML/2.8/tischendorfmorph.OSIS.xml"


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
        _transliterate(records, func=transliterate_hebrew)

    elif translation == "grtisch":
        path = _download_grtisch()
        records = parse_osis(path, w_tag_parser="greek")
        _transliterate(records, func=transliterate_greek)

    return records


def _download_hewlc(book_id):
    url = f"{_HEWLC_ROOT_URL}/{book_id}.xml"
    path = get_cache_path("raw", "hewlc", f"{book_id.lower()}_osis.xml")
    download(url, path)
    return path


def _download_grtisch():
    path = get_cache_path("raw", "grtisch", "grtisch_osis.xml")
    download(_GRTISCH_URL, path)
    return path


def _transliterate(records, func):
    for record in records:
        for token in record["tokens"]:
            token["tlit"] = func(token["text"])
