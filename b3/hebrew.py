import json
import logging
from pathlib import Path
import re
import sys

import boto3
import requests

from b3.oshb import parse_oshb_xml


_BOOK_IDS = [
    'Gen', 'Exod', 'Lev', 'Num', 'Deut', 'Josh', 'Judg', '1Sam', '2Sam', '1Kgs', '2Kgs', 
    'Isa', 'Jer', 'Ezek', 'Hos', 'Joel', 'Amos', 'Obad', 'Jonah', 'Mic', 'Nah', 'Hab', 'Zeph', 'Hag', 'Zech', 'Mal',
    'Ps', 'Prov', 'Job', 'Song', 'Ruth', 'Lam', 'Eccl', 'Esth', 'Dan', 'Ezra', 'Neh', '1Chr', '2Chr',
]
_CACHE_DIR = Path(__file__).parent.parent / ".cache"
_ROOT_URL = "https://raw.githubusercontent.com/openscriptures/morphhb/master/wlc"


def populate_hebrew(limit):
    """
    Parse openscriptures xml-files and make my own json ones, then upload to dynamodb.
    """
    uploaded = 0
    for book_id in _BOOK_IDS:
        logging.info(f"Working on {book_id}")
        _download_file(book_id)
        _parse_file(book_id)
        uploaded = _upload(book_id, uploaded, limit)
        logging.info(f"Uploaded {uploaded} records")
        if uploaded >= limit:
            logging.warning(f"Reached limit of {limit} - stopping!")
            break


def _download_file(book_id):
    dir_ = _CACHE_DIR / "b3-heb-raw"
    dir_.mkdir(parents=True, exist_ok=True)
    path = dir_ / f"{book_id}.xml"
    if not path.exists():
        url = f"{_ROOT_URL}/{book_id}.xml"
        logging.info(f"Requesting {url}")
        r = requests.get(url)
        with path.open('wb') as f:
            f.write(r.content)


def _parse_file(book_id):
    path = _CACHE_DIR / "b3-heb-raw" / f"{book_id}.xml"
    parsed = parse_oshb_xml(path)
    dir_ = _CACHE_DIR / "b3-heb"
    dir_.mkdir(parents=True, exist_ok=True)
    path = dir_ / f"{book_id}.json"
    with path.open("w", encoding="utf8") as f:
        json.dump(parsed, f)


def _upload(book_id, uploaded, limit):
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table('B3Bibles')
    path = _CACHE_DIR / "b3-heb" / f"{book_id}.json"
    with table.batch_writer() as batch:
        with path.open("r", encoding="utf8") as f:
            records = json.load(f)
        logging.info(f"Uploading {len(records)} from {path.name}")
        for record in records:
            batch.put_item(Item=record)
            uploaded += 1
            if uploaded >= limit:
                break
    return uploaded