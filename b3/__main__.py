import json
import logging
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

import boto3
import click
import requests


fmt = "%(asctime)s : %(levelname)s : %(message)s"
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format=fmt)


_BOOK_IDS = [
    'Gen', 'Exod', 'Lev', 'Num', 'Deut', 'Josh', 'Judg', '1Sam', '2Sam', '1Kgs', '2Kgs', 
    'Isa', 'Jer', 'Ezek', 'Hos', 'Joel', 'Amos', 'Obad', 'Jonah', 'Mic', 'Nah', 'Hab', 'Zeph', 'Hag', 'Zech', 'Mal',
    'Ps', 'Prov', 'Job', 'Song', 'Ruth', 'Lam', 'Eccl', 'Esth', 'Dan', 'Ezra', 'Neh', '1Chr', '2Chr',
]
_CACHE_DIR = Path(__file__).parent.parent / ".cache"
_ROOT_URL = "https://raw.githubusercontent.com/openscriptures/morphhb/master/wlc"


@click.group()
def cli():
    """
    Main click group.
    """


@cli.command("populate-db")
@click.option("--limit", default=31, help="Limit number of records uploaded to dynamodb.")
def populate_db(limit):
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
    dir_ = _CACHE_DIR / "b3-heb"
    dir_.mkdir(parents=True, exist_ok=True)
    path = dir_ / f"{book_id}.json"
    tree = _parse_xml(book_id)
    tokens = list(_tokenize(book_id, tree))
    grouped = list(_group_tokens(tokens))
    with path.open("w", encoding="utf8") as f:
        json.dump(grouped, f)


def _upload(book_id, uploaded, limit):
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table('b3-books')
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


def _parse_xml(book_id):
    path = _CACHE_DIR / "b3-heb-raw" / f"{book_id}.xml"
    with path.open("r") as f:
        xmlstring = re.sub(' xmlns="[^"]+"', '', f.read(), count=1)
    return ET.fromstring(xmlstring)


def _tokenize(book_id, tree):
    """
    Make a list of verses with the following schema:
    - chapter_osis_id: the OSIS ID for a chapter
    - verse: verse number
    - token: the token
    - strongs: (optional) strongs reference
    """
    for verse in tree.findall("*/div/chapter/verse"):
        root = _parse_osis_id(verse.attrib["osisID"])
        for elem in verse.findall('*'):
            if elem.tag == "note" and (elem.text or "").startswith("KJV:"):
                # Use KJV versification
                root = _parse_osis_id(elem.text.replace("KJV:", "").strip("!abcd"))
            elif elem.tag == "w":
                # TODO: Split these up smaller based on "/" chars
                # TODO: ...and handle whitespace
                token = elem.text.replace("/", "")
                strongs = re.sub(r"\D", "", elem.attrib["lemma"]) or None
                yield {**root, **{"token": token, "strongs": strongs}}
            elif elem.tag == 'seg':
                seg = {
                    'x-maqqef': '\u05BE',
                    'x-paseq': ' \u05C0 ',
                    'x-pe': ' (\u05E4) ',
                    'x-reversednun': ' (\u05C6) ',  # <- Appears in some Psalms
                    'x-samekh': ' (\u05E1) ',
                    'x-sof-pasuq': '\u05C3 ',
                }[elem.attrib['type']]
                yield {**root, **{"token": seg}}


def _group_tokens(tokens):
    prev_vid = None
    buffer = []
    for x in tokens:
        vid = {"chapter_osis_id": x.pop("chapter_osis_id"), "verse": x.pop("verse")}
        if prev_vid and prev_vid != vid:
            yield {**prev_vid, **{"tokens": buffer}}
            buffer = []
        prev_vid = vid
        buffer.append(x)
    yield {**vid, **{"tokens": buffer}}


def _parse_osis_id(ref):
    cid, vnum = ref.rsplit('.', 1)
    return {"chapter_osis_id": cid, "verse": int(vnum)}


cli()  # pylint: disable=no-value-for-parameter
