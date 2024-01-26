import re

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
    """Create LXX stuff."""
    records = []
    for code, fname in _FILES.items():
        path = _download(fname)
        records.extend(_parse(code, path))
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
            else:
                _append_token(record, line)
    
        if record and record["tokens"]:
            yield record


def _append_token(record, line):
    for word in line.split("\t")[-1].split():
        root = {"chapterId": record["chapterId"], "verseNum": record["verseNum"]}
        greek = _to_greek(word)
        if greek:
            record["tokens"].append({**root, **{"text": greek + " ", "type": "o"}})


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