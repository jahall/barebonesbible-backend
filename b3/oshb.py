"""
Code to parse Openscriptures Hebrew Bible xml format.
"""
from itertools import zip_longest
import json
import re
import xml.etree.ElementTree as ET


def parse_oshb_xml(path, use_kjv_versification=True):
    """
    Parse the OSHB xml file into a list of json-ified verses.
    """
    tree = _parse_xml(path)
    tokens = list(_tokenize(tree, use_kjv_versification))
    return list(_group_tokens(tokens))


def _parse_xml(path):
    with path.open("r") as f:
        xmlstring = re.sub(' xmlns="[^"]+"', '', f.read(), count=1)
    return ET.fromstring(xmlstring)


def _tokenize(tree, use_kjv_versification):
    """
    Make a list of verses with the following schema:
    - chapter_osis_id: the OSIS ID for a chapter
    - verse: verse number
    - token: the token
    - strongs: (optional) strongs reference
    """
    for verse in tree.findall("*/div/chapter/verse"):
        root = _parse_osis_id(verse.attrib["osisID"])
        is_first = True
        for elem in verse.findall('*'):
            if use_kjv_versification and elem.tag == "note" and (elem.text or "").startswith("KJV:"):
                root = _parse_osis_id(elem.text.replace("KJV:", "").strip("!abcd"))
            elif elem.tag == "w":
                if not is_first:
                    yield {**root, **{"text": " ", "type": "space"}}  # add whitespace
                for code, text in zip_longest(elem.attrib["lemma"].split("/"), elem.text.split("/")):
                    code = code.split()[0] if code else ""
                    if code.isdigit():
                        yield {**root, **{"text": text, "type": "word", "code": "H" + code}}
                    else:
                        yield {**root, **{"text": text, "type": "prefix" if code else "suffix"}}
                is_first = False
            elif elem.tag == 'seg':
                # TODO: handle these spaces!!
                seg = {
                    'x-maqqef': '\u05BE',
                    'x-paseq': ' \u05C0 ',
                    'x-pe': ' (\u05E4) ',
                    'x-reversednun': ' (\u05C6) ',  # <- Appears in some Psalms
                    'x-samekh': ' (\u05E1) ',
                    'x-sof-pasuq': '\u05C3 ',
                }[elem.attrib['type']]
                yield {**root, **{"text": seg, "type": "punc"}}


def _group_tokens(tokens):
    """
    Group tokens by verse.
    """
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