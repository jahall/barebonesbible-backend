import json
import logging
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

import requests

#from b3.hebrew import Hebrew

#HEB = Hebrew()

_BOOK_IDS = [
    'Gen', 'Exod', 'Lev', 'Num', 'Deut', 'Josh', 'Judg', '1Sam', '2Sam', '1Kgs', '2Kgs', 
    'Isa', 'Jer', 'Ezek', 'Hos', 'Joel', 'Amos', 'Obad', 'Jonah', 'Mic', 'Nah', 'Hab', 'Zeph', 'Hag', 'Zech', 'Mal',
    'Ps', 'Prov', 'Job', 'Song', 'Ruth', 'Lam', 'Eccl', 'Esth', 'Dan', 'Ezra', 'Neh', '1Chr', '2Chr',
]
_CACHE_DIR = Path(__file__).parent.parent / ".cache"
_ROOT_URL = "https://raw.githubusercontent.com/openscriptures/morphhb/master/wlc"


def run():
    """Parse openscriptures xml-files and make my own json ones."""
    logging.info("Downloading openscriptures xml files")
    _download_files()
    logging.info("Parsing openscriptures xml files")
    _parse_files()


def _download_files():
    dir_ = _CACHE_DIR / "b3-heb-raw"
    dir_.mkdir(parents=True, exist_ok=True)
    for book_id in _BOOK_IDS:
        path = dir_ / f"{book_id}.xml"
        if not path.exists():
            logging.info(f"Requesting {book_id}")
            r = requests.get(f"{_ROOT_URL}/{book_id}.xml")
            with path.open('wb') as f:
                f.write(r.content)


def _parse_files():
    dir_ = _CACHE_DIR / "b3-heb"
    dir_.mkdir(parents=True, exist_ok=True)
    for book_id in _BOOK_IDS:
        path = dir_ / f"{book_id}.json"
        print('Creating {}'.format(path))
        tree = _parse_xml(book_id)
        tokens = list(_tokenize(book_id, tree))
        grouped = list(_group_tokens(tokens))
        with path.open("w") as f:
            json.dump(grouped, f)


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
                strongs = re.sub("\D", "", elem.attrib["lemma"]) or None
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


def _parse_w_elem(elem):
    w = HEB.strip_cantillations(elem.text.replace('/',''))
    ws = HEB.strip_niqqud(w)
    tw = HEB.transliterate(w)
    strongs = re.sub('\D', '', elem.attrib['lemma']) or None
    if strongs:
        strongs = 'H' + strongs
    return [w, ws, tw, strongs, '', '']



if __name__ == '__main__':
    fmt = "%(asctime)s : %(levelname)s : %(message)s"
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format=fmt)
    run()
