import json
import logging
import re
import unicodedata

from functools import lru_cache

from .translit import transliterate_greek
from .utils import download, get_cache_path


_URL = "https://ccat.sas.upenn.edu/gopher/text/religion/biblical/parallel/{file}.par"
_FILES = {
    # Torah
    "Gen": "01.Genesis",
    "Exod": "02.Exodus",
    "Lev": "03.Lev",
    "Num": "04.Num",
    "Deut": "05.Deut",
    # Neviim
    "Josh": "06.JoshB",  # or 07.JoshA
    "Judg": "08.JudgesB",  # or 09.JudgesA
    "1Sam": "11.1Sam",
    "2Sam": "12.2Sam",
    "1Kgs": "13.1Kings",
    "2Kgs": "14.2Kings", 
    "Isa": "40.Isaiah",
    "Jer": "41.Jer",
    "Ezek": "44.Ezekiel",
    "Hos": "28.Hosea",
    "Joel": "31.Joel",
    "Amos": "30.Amos",
    "Obad": "33.Obadiah",
    "Jonah": "32.Jonah",
    "Mic": "29.Micah",
    "Nah": "34.Nahum",
    "Hab": "35.Hab",
    "Zeph": "36.Zeph",
    "Hag": "37.Haggai",
    "Zech": "38.Zech",
    "Mal": "39.Malachi",
    # Ketuviim
    "Ps": "20.Psalms",
    "Prov": "23.Prov",
    "Job": "26.Job",
    "Song": "25.Cant",
    "Ruth": "10.Ruth",
    "Lam": "43.Lam",
    "Eccl": "24.Qoh",
    "Esth": "18.Esther",
    "Dan": "45.DanielOG",  # or 46.DanielTh
    "Ezra": "18.Ezra",
    "Neh": "19.Neh",
    "1Chr": "15.1Chron",
    "2Chr": "16.2Chron",
}


def create_lxx():
    """Create LXX records."""
    records = []
    for code, fname in _FILES.items():
        logging.info(f"Working on {code}")
        path = _download(fname)
        records.extend(_parse(code, path))

    logging.info("Performing transliteration")
    for record in records:
        for token in record["tokens"]:
            token["tlit"] = transliterate_greek(token["text"])
    return records


def _download(fname):
    url = _URL.format(file=fname)
    path = get_cache_path("raw", "grlxx", f"{fname}.par")
    download(url, path)
    return path

  
def _parse(code, path):
    with path.open() as f:
        record = None
        for line in f:
            # ignore empty lines
            line = line.strip()
            if line == "":
                continue

            # start new verse
            if re.match(r".*\s+\d+:\d+$", line) or line.startswith("Obad"):
                if record and record["tokens"]:
                    yield record
                cv = line.split()[-1].split(":")
                c = 1 if len(cv) == 1 else cv[0]
                v = cv[0] if len(cv) == 1 else cv[1]
                record = {"chapterId": f"{code}.{c}", "verseNum": int(v), "tokens": []}

            # append greek
            elif "\t" in line:
                _append_token(record, line)
    
        if record and record["tokens"]:
            yield record


def _append_token(record, line):
    # 1. Split hebrew and greek
    hebrew_repr, greek_repr = line.split("\t")[:2]

    # 2. Map the hebrew to strongs refs
    prefix = record["chapterId"], record["verseNum"]
    strongs = []
    for word in hebrew_repr.split():
        word = word.split("/")[-1]
        word = "".join(c for c in word if c in _VALID_HEBREW_REPRS)
        for ref in strongs_map().get(prefix + (word,), []):
            if ref not in strongs:
                strongs.append(ref)

    # 3. Decode the greek
    phrase = (_to_greek(word) for word in greek_repr.split())
    phrase = [word for word in phrase if word]
    if not phrase:
        return
    if record["tokens"]:
        record["tokens"].append({"text": " ", "type": "punc"})

    # no strongs ref so just return
    if not strongs:
        record["tokens"].append({"text": " ".join(phrase), "type": "o"})
        return

    # exclude non-important words in the highlighting
    while len(phrase) > 1 and phrase[0] in _GREEK_CRUFT:
        record["tokens"].append({"text": phrase[0] + " ", "type": "o"})
        phrase = phrase[1:]
    record["tokens"].append({"text": " ".join(phrase), "type": "w", "strongs": strongs})


def _to_greek(word: str) -> str:
    greek = ""
    if word.startswith("{") or word.startswith("["):
        return greek
    upper = False
    for char in word:
        if char == "*":
            upper = True
        else:
            char = _TO_GREEK.get(char)
            if char:
                greek += char.upper() if upper else char
            upper = False
    return greek


_GREEK_CRUFT = {
    "εν",
    "εκ",
    "εισ",
    "και",
    "τα",
    "ται",
    "τη",
    "τησ",
    "την",
    "το",
    "του",
    "τον",
    "τω",
    "τωυ",
    "των",
    "ο",
}

_TO_GREEK = {
    "A": "\u03B1",  # alpha
    "B": "\u03B2",  # beta
    "G": "\u03B3",  # gamma
    "D": "\u03B4",  # delta
    "E": "\u03B5",  # epsilon
    "Z": "\u03B6",  # zeta
    "H": "\u03B7",  # eta
    "Q": "\u03B8",  # theta
    "I": "\u03B9",  # iota
    "K": "\u03BA",  # kappa
    "L": "\u03BB",  # lambda
    "M": "\u03BC",  # mu
    "N": "\u03BD",  # nu
    "C": "\u03BE",  # xi
    "O": "\u03BF",  # omicron
    "P": "\u03C0",  # pi
    "R": "\u03C1",  # rho
    "J": "\u03C2",  # sigma (final)
    "S": "\u03C3",  # sigma
    "T": "\u03C4",  # tau
    "U": "\u03C5",  # upsilon
    "F": "\u03C6",  # phi
    "X": "\u03C7",  # chi
    "Y": "\u03C8",  # psi
    "W": "\u03C9",  # omega
    "V": "\u03DD",  # digamma (archaic!)
}


@lru_cache(maxsize=1)
def strongs_map():
    """Mapping from (chapter, verse, word-repr) -> list of strongs refs."""
    path = get_cache_path("staging", "hewlc.json")
    if not path.exists():
        raise ValueError("We need to stage `hewlc` before we can do `grlxx`")
    
    strongs = {}
    with path.open(encoding="utf8") as f:
        for verse in json.load(f):
            prefix = verse["chapterId"], verse["verseNum"]
            for token in verse["tokens"]:
                if token["type"] == "w":
                    word = _to_hebrew_tlit(token["text"])
                    if word not in _IGNORE:
                        strongs[prefix + (word,)] = token["strongs"]
    return strongs
                
                
def _to_hebrew_tlit(word: str) -> str:
    word = unicodedata.normalize("NFD", word)  # ensure chars and accents are separated
    return "".join(_TO_HEBREW_REPR.get(char, "") for char in word)


_IGNORE = {"E)N", ")T"}


_TO_HEBREW_REPR = {
    # main chars
    "\u05D0": ")",
    "\u05D1": "B",
    "\u05D2": "G",
    "\u05D3": "D",
    "\u05D4": "H",
    "\u05D5": "W",
    "\u05D6": "Z",
    "\u05D7": "X",
    "\u05D8": "+",
    "\u05D9": "Y",
    "\u05DA": "K",  # final
    "\u05DB": "K",
    "\u05DC": "L",
    "\u05DD": "M",  # final
    "\u05DE": "M",
    "\u05DF": "N",  # final
    "\u05E0": "N",
    "\u05E1": "S",
    "\u05E2": "(",
    "\u05E3": "P",  # final
    "\u05E4": "P",
    "\u05E5": "C",  # final
    "\u05E6": "C",
    "\u05E7": "Q",
    "\u05E8": "R",
    # "\u05E9": "#",  <- only need the relevant dot below
    "\u05C1": "$",  # shin-dot
    "\u05C2": "&",  # sin-dot
    "\u05EA": "T",
}

_VALID_HEBREW_REPRS = set(_TO_HEBREW_REPR.values())
