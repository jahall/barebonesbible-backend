import json
import logging
from pathlib import Path
import re
import sys

import boto3
import requests

from .utils import parse_xml


_CACHE_DIR = Path(__file__).parent.parent / ".cache"
_ROOT_URL = "https://raw.githubusercontent.com/gratis-bible/bible/master/en"


def populate_english(translation, limit):
    """
    Parse openscriptures xml-files and make my own json ones, then upload to dynamodb.
    """
    translation = translation.lower()
    logging.info(f"Downloading {translation}.xml")
    _download_file(translation)
    records = _parse_file(translation)
    logging.info(f"Parsed {len(records)} verses")
    records = records[:limit]
    logging.info(f"Uploading {len(records)} records")
    _upload(records)


def _download_file(translation):
    dir_ = _CACHE_DIR / "b3-en-raw"
    dir_.mkdir(parents=True, exist_ok=True)
    path = dir_ / f"{translation}.xml"
    if not path.exists():
        url = f"{_ROOT_URL}/{translation}.xml"
        logging.info(f"Requesting {url}")
        r = requests.get(url)
        with path.open('wb') as f:
            f.write(r.content)


def _parse_file(translation):
    path = _CACHE_DIR / "b3-en-raw" / f"{translation}.xml"
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
    return records


def _upload(records):
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table('B3Bibles')
    with table.batch_writer() as batch:
        for record in records:
            batch.put_item(Item=record)
