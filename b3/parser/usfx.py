import itertools
from pathlib import Path
import re
import xml.etree.ElementTree as ET


def parse_usfx(path):
    """
    Parse mental USFX format to big list of tokenized verses.
    """
    with Path(path).open("r", encoding="utf8") as f:
        xmlstr = f.read()
        xmlstr = re.sub(r" xmlns=['\"][^'\"]+['\"]", "", xmlstr, count=1)
        xmlstr = re.sub(r"</?wj>", "", xmlstr)
    tree = ET.fromstring(xmlstr)
    token_iter = _iter_tokens(tree)
    grouper = itertools.groupby(token_iter, key=lambda x: x[0])
    records = [
        {
            "chapterId": cid,
            "verseNum": vnum,
            "tokens": [tokens for _, tokens in group],
        }
        for (cid, vnum), group in grouper
    ]
    return records
    
    
def _iter_tokens(tree):
    """
    Iterate over every token in every verse.
    """
    vid = None
    for e in tree.iter():  # iterates recursively through the doc
        # Handle verse count
        if e.tag in {"book", "ve"}:
            vid = None
        elif e.tag == "v":
            vid = _extract_verse_id(e)
        # Handle tokens
        if vid and e.tag in {"w"}:
            token = {"type": "w", "text": e.text}
            if "s" in e.attrib:
                token["strongs"] = e.attrib["s"].split()
            yield vid, token
        if vid and e.tag in {"p", "q", "qs"} and e.text:
            yield vid, {"type": "o", "text": e.text.replace("\n", " ")}
        if vid and e.tag in {"w", "f"} and e.tail:
            yield vid, {"type": "o", "text": e.tail.replace("\n", " ")}
            
            
def _extract_verse_id(e):
    bookid, cnum, vnum = e.attrib["bcv"].split(".")
    cid = f"{_usfx_to_osis(bookid)}.{cnum}"
    vnum = int(vnum)
    return cid, vnum


def _usfx_to_osis(usfx_id):
    """
    Normalize book refs to OSIS.
    """
    return {
        # Torah
        "Exo": "Exod",
        "Deu": "Deut",
        # Neviim
        "Jos": "Josh",
        "Jdg": "Judg",
        "1Sa": "1Sam",
        "2Sa": "2Sam",
        "1Ki": "1Kgs",
        "2Ki": "2Kgs",
        "Ezk": "Ezek",
        "Jol": "Joel",
        "Amo": "Amos",
        "Oba": "Obad",
        "Jon": "Jonah",
        "Zep": "Zeph",
        "Zec": "Zech",
        # Ketuvim
        "Psa": "Ps",
        "Pro": "Prov",
        "Sng": "Song",
        "Rut": "Ruth",
        "Ecc": "Eccl",
        "Est": "Esth",
        "Ezr": "Ezra",
        "1Ch": "1Chr",
        "2Ch": "2Chr",
        # New Testament
        "Mat": "Matt",
        "Mrk": "Mark",
        "Luk": "Luke",
        "Jhn": "John",
        "Act": "Acts",
        "1Co": "1Cor",
        "2Co": "2Cor",
        "Php": "Phil",
        "1Th": "1Thess",
        "2Th": "2Thess",
        "1Ti": "1Tim",
        "2Ti": "2Tim",
        "Tit": "Titus",
        "Phm": "Phlm",
        "1Pe": "1Pet",
        "2Pe": "2Pet",
        "1Jn": "1John",
        "2Jn": "2John",
        "3Jn": "3John",
        "Jud": "Jude",
    }.get(usfx_id.title(), usfx_id.title())