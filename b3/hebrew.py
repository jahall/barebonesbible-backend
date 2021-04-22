from itertools import zip_longest
import json
import logging
import re
import unicodedata

import requests

from .translit import Hebrew
from .utils import get_cache_path, parse_xml


_BOOK_IDS = [
    "Gen", "Exod", "Lev", "Num", "Deut", "Josh", "Judg", "1Sam", "2Sam", "1Kgs", "2Kgs", 
    "Isa", "Jer", "Ezek", "Hos", "Joel", "Amos", "Obad", "Jonah", "Mic", "Nah", "Hab", "Zeph", "Hag", "Zech", "Mal",
    "Ps", "Prov", "Job", "Song", "Ruth", "Lam", "Eccl", "Esth", "Dan", "Ezra", "Neh", "1Chr", "2Chr",
]
_ROOT_URL = "https://raw.githubusercontent.com/openscriptures/morphhb/master/wlc"
_HEB = Hebrew()


def fetch_hebrew():
    """
    Parse openscriptures xml-files and make my own json ones, then upload to dynamodb.
    """
    records = []
    for book_id in _BOOK_IDS:
        logging.info(f"Working on {book_id}")
        path = _download_file(book_id)
        records.extend(_parse_oshb_xml(path))
    logging.info("Performing transliteration")
    _transliterate(records)
    return records


def _download_file(book_id):
    path = get_cache_path("raw", "wlc", f"{book_id}.xml")
    if not path.exists():
        url = f"{_ROOT_URL}/{book_id}.xml"
        logging.info(f"Requesting {url}")
        r = requests.get(url)
        with path.open("wb") as f:
            f.write(r.content)
    return path


def _parse_oshb_xml(path, use_kjv_versification=True):
    """
    Parse the OSHB xml file into a list of json-ified verses.
    """
    tree = parse_xml(path)
    tokens = _tokenize(tree, use_kjv_versification)
    return list(_group_tokens(tokens))


def _tokenize(tree, use_kjv_versification):
    """
    Make a list of verses with the following schema:
    - chapter_osis_id: the OSIS ID for a chapter
    - verse: verse number
    - token: the token
    - strongs: (optional) strongs reference
    """
    tokens = []
    for verse in tree.findall("*/div/chapter/verse"):
        root = _parse_osis_id(verse.attrib["osisID"])
        for elem in verse.findall('*'):
            if use_kjv_versification and elem.tag == "note" and (elem.text or "").startswith("KJV:"):
                root = _parse_osis_id(elem.text.replace("KJV:", "").strip("!abcd"))
            elif elem.tag == "w":
                for code, text in zip_longest(elem.attrib["lemma"].split("/"), elem.text.split("/")):
                    code = code.split()[0] if code else ""
                    text = unicodedata.normalize("NFD", text or "")  # ensure chars and accents are separated
                    if code.isdigit():
                        tokens.append({**root, **{"text": text, "type": "w", "strongs": ["H" + code]}})
                    else:
                        tokens.append({**root, **{"text": text, "type": "pre" if code else "suf"}})
            elif elem.tag == 'seg':
                # TODO: handle these spaces!!
                seg = {
                    'x-maqqef': '\u05BE',
                    'x-paseq': '\u05C0',
                    'x-pe': '(\u05E4)',
                    'x-reversednun': '(\u05C6)',  # <- Appears in some Psalms
                    'x-samekh': '(\u05E1)',
                    'x-sof-pasuq': '\u05C3',
                }[elem.attrib['type']]
                if tokens[-1]["type"] == "punc":
                    tokens[-1]["text"] += seg
                else:
                    tokens.append({**root, **{"text": seg, "type": "punc"}})
            if elem.tail:
                tail = elem.tail.replace("\n", " ")
                tail = re.sub(r"\s+", " ", tail)
                if tokens[-1]["type"] == "punc":
                    tokens[-1]["text"] += tail
                else:
                    tokens.append({**root, **{"text": tail, "type": "punc"}})
    return tokens


def _group_tokens(tokens):
    """
    Group tokens by verse.
    """
    prev_vid = None
    buffer = []
    for x in tokens:
        vid = {"chapterId": x.pop("chapterId"), "verseNum": x.pop("verseNum")}
        if prev_vid and prev_vid != vid:
            yield {**prev_vid, **{"tokens": buffer}}
            buffer = []
        prev_vid = vid
        buffer.append(x)
    yield {**vid, **{"tokens": buffer}}


def _parse_osis_id(ref):
    cid, vnum = ref.rsplit('.', 1)
    return {"chapterId": cid, "verseNum": int(vnum)}


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
