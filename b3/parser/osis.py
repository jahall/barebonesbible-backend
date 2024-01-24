from itertools import zip_longest
from pathlib import Path
import re
import unicodedata
import xml.etree.ElementTree as ET


def parse_osis(path, w_tag_parser="default", use_kjv_versification=True):
    """
    Parse the OSIS xml file into a list of json-ified verses.
    """
    with Path(path).open("r", encoding="utf8") as f:
        xmlstr = f.read()
        xmlstr = re.sub(r" xmlns=['\"][^'\"]+['\"]", "", xmlstr, count=1)
        xmlstr = re.sub(r'\<seg type="x\-small"\>(.*?)\</seg\>', r"\g<1>", xmlstr)
        xmlstr = re.sub(r'\<seg type="x\-large"\>(.*?)\</seg\>', r"\g<1>", xmlstr)
        xmlstr = re.sub(r'\<seg type="x\-suspended"\>(.*?)\</seg\>', r"\g<1>", xmlstr)
    if isinstance(w_tag_parser, str):
        w_tag_parser = _W_TAG_PARSERS[w_tag_parser]
    tree = ET.fromstring(xmlstr)
    tokens = _tokenize(tree, w_tag_parser, use_kjv_versification)
    return list(_group_tokens(tokens))


def _tokenize(tree, w_tag_parser, use_kjv_versification):
    """
    Make a list of verses with the following schema:
    - chapter_osis_id: the OSIS ID for a chapter
    - verse: verse number
    - token: the token
    - strongs: (optional) strongs reference
    """
    tokens = []
    root = None
    ignore = 0
    for elem in tree.iter():
        # Ignore everything within a note
        if ignore:
            ignore = max(ignore - 1, 0)
            continue
        ignore = max(ignore - 1, 0)
        if elem.tag == "note":
            ignore = _n_descendents(elem)

        # Handle verses
        if elem.tag == "verse" and "osisID" in elem.attrib:
            root = _parse_osis_id(elem.attrib["osisID"])
        elif elem.tag == "verse" and "eID" in elem.attrib:
            root = None
        elif use_kjv_versification and elem.tag == "note" and (elem.text or "").startswith("KJV:"):
            root = _parse_osis_id(elem.text.replace("KJV:", "").strip("!abcd"))

        # Ignore non-words and segs
        if elem.tag not in {"w", "seg"}:
            continue

        if elem.tag == "w" and elem.text:
            text = unicodedata.normalize("NFD", elem.text or "")  # ensure chars and accents are separated
            for type_, text, strongs in w_tag_parser(elem.text, lemma=elem.attrib["lemma"]):
                tokens.append({**root, **{"type": type_, "text": text, "strongs": strongs}})

        elif elem.tag == 'seg':
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
                tokens.append({**root, **{"type": "punc", "text": seg}})
    
        if elem.tail:
            tail = elem.tail.replace("\n", " ")
            tail = re.sub(r"\s+", " ", tail)
            if tokens[-1]["type"] == "punc":
                tokens[-1]["text"] += tail
            else:
                tokens.append({**root, **{"type": "punc", "text": tail}})
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


def _parse_default_w_tag(text, lemma=None):
    yield "w", text, []


def _parse_gr_w_tag(text, lemma=None):
    """
    For example:
    
        <w lemma="strong:G976 lemma:βίβλος" morph="robinson:N-NSF">Βίβλος</w>

    Would become:

        "w", "Βίβλος", ["G976"]
    """
    data = {}
    if lemma:
        data = (item.split(":") for item in lemma.strip().split() if ":" in item)
        data = {k: v for k, v in data}
    strongs = [data["strong"]] if "strong" in data else []
    yield "w", text, strongs


def _parse_he_w_tag(text, lemma=None):
    """
    For example:
    
        <w lemma="c/8659" n="1" morph="HC/Np/Sh" id="13GzE">וְ/תַרְשִׁ֑ישָׁ/ה</w>

    Would become (note: currently ignoring suffixes):

        "pre", "וְ", []
        "w", "תַרְשִׁ֑ישָׁה", ["H8659"]
    """
    splits = lemma.count("/")
    texts = text.split("/", splits)
    codes = lemma.split("/")
    for text, code in zip(texts, codes):
        text = text.replace("/", "")
        code = code.split()[0]
        if code.isdigit():
            type_ = "w"
            strongs = ["H" + code]
        else:
            type_ = "pre"
            strongs = []
        yield type_, text, strongs    


def _n_descendents(elem):
    return len(list(elem.iter())) - 1


def _parse_osis_id(ref):
    cid, vnum = ref.rsplit('.', 1)
    return {"chapterId": cid, "verseNum": int(vnum)}


_W_TAG_PARSERS = {
    "default": _parse_default_w_tag,
    "hebrew": _parse_he_w_tag,
    "greek": _parse_gr_w_tag,
}