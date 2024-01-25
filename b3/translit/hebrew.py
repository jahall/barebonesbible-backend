import re
import unicodedata


def transliterate_hebrew(phrase, reverse=False):
    """
    Transliterate to english.
    """
    phrase = unicodedata.normalize("NFD", phrase)  # ensure chars and accents are separated
    phrase = _strip_cantillations(phrase)
    tlit = "".join([_tlit(clump) for clump in _iter_clumps(phrase)])
    for seq, sub in _TRANSLIT_SUBS:
        tlit = re.sub(seq, sub, tlit)
    tlit = " ".join(tlit.split()[::-1]) if reverse else tlit
    return tlit.lower()   # <- lower looks a bit nicer
        

def _strip_cantillations(phrase):
    """
    Strip all cantillations.
    """
    phrase = _CANTILLATIONS_RE.sub("", phrase)
    return phrase.replace(_NIQQUD["meteg"], "")  # Meteg is messing with css-font :(


def _tlit(clump):
    tlit = None
    for tmap in [_CONS_TMAP, _VOWEL_TMAP, _PUNC_TMAP]:
        for i in range(len(clump), 0, -1):
            tlit_ = tmap.get(clump[:i])
            if tlit_ is not None:
                tlit = (tlit or '') + tlit_
                clump = clump[i:]
                break
    return clump if tlit is None else tlit


def _iter_clumps(phrase):
    """
    Iterate over "clumps" of unicode chars, where each clump contains a letter and all
    the associated accents i.e. niqqud and cantillations.
    """
    if phrase:
        clump = phrase[0]
        ignore = {_NIQQUD[i] for i in ["meteg", "rafe", "upper-dot", "lower-dot"]}
        accents = set(_CANTILLATIONS.values()) | set(_NIQQUD.values())
        for c in phrase[1:]:
            if c in ignore:
                continue
            if c in accents:
                clump += c
            else:
                yield _sort_clump(clump)
                clump = c
        yield _sort_clump(clump)


def _sort_clump(clump):
    """
    Ensure accents appear in consistent order.
    """

    def key(char):
        if char in {_MAP["shin-dot"], _MAP["sin-dot"]}:
            return 0
        elif char in {_MAP["dagesh"]}:
            return 1
        else:
            return 2

    return clump[0] + "".join(sorted(clump[1:], key=key))


_CANTILLATIONS_RE = re.compile("[\u0591-\u05AF]")
_CANTILLATIONS = {
    "etnahta": "\u0591",
    "segol-acc": "\u0592",  # To avoid clash with the niqqud segol
    "shalshelet": "\u0593",
    "zaqef-qatan": "\u0594",
    "zaqef-gadol": "\u0595",
    "tipeha": "\u0596",
    "revia": "\u0597",
    "zarqa": "\u0598",
    "pashta": "\u0599",
    "yetiv": "\u059A",
    "tevir": "\u059B",
    "geresh": "\u059C",
    "geresh-muqdam": "\u059D",
    "gershayim": "\u059E",
    "qarney-para": "\u059F",
    "telisha-gedola": "\u05A0",
    "pazer": "\u05A1",
    "atnah-hafukh": "\u05A2",
    "munah": "\u05A3",
    "mahapakh": "\u05A4",
    "merkha": "\u05A5",
    "merkha-kefula": "\u05A6",
    "darga": "\u05A7",
    "qadma": "\u05A8",
    "telisha-qetana": "\u05A9",
    "yerah-ben-yomo": "\u05AA",
    "ole": "\u05AB",
    "iluy": "\u05AC",
    "dehi": "\u05AD",
    "zinor": "\u05AE",
    "masora-circle": "\u05AF",
}
_NIQQUD = {
    "sheva": "\u05B0",
    "hataf-segol": "\u05B1",
    "hataf-patah": "\u05B2",
    "hataf-qamats": "\u05B3",
    "hireq": "\u05B4",
    "tsere": "\u05B5",
    "segol": "\u05B6",
    "patah": "\u05B7",
    "qamats": "\u05B8",
    "holam": "\u05B9",
    "holam-haser": "\u05BA",
    "qubuts": "\u05BB",
    "dagesh": "\u05BC",
    "meteg": "\u05BD",  # <- for stress-marking
    "rafe": "\u05BF",   # <- opposite of dagesh
    "shin-dot": "\u05C1",
    "sin-dot": "\u05C2",
    "upper-dot": "\u05C4",
    "lower-dot": "\u05C5",
    #"qamats-qatan": "\u05C7",  # <- Not used
}
_PUNCTUATION = {
    "maqaf": "\u05BE",
    "paseq": "\u05C0",
    "sof-pasuq": "\u05C3",
    "nun-hafukha": "\u05C6",
}
_CHARS = {
    "aleph": "\u05D0",
    "bet": "\u05D1",
    "gimmel": "\u05D2",
    "dalet": "\u05D3",
    "heh": "\u05D4",
    "vav": "\u05D5",
    "zayin": "\u05D6",
    "het": "\u05D7",
    "tet": "\u05D8",
    "yud": "\u05D9",
    "kaf": "\u05DB",
    "lamed": "\u05DC",
    "mem": "\u05DE",
    "nun": "\u05E0",
    "samekh": "\u05E1",
    "ayin": "\u05E2",
    "peh": "\u05E4",
    "tsadi": "\u05E6",
    "qof": "\u05E7",
    "resh": "\u05E8",
    "shin": "\u05E9",
    "tav": "\u05EA",

    "f-kaf": "\u05DA",
    "f-mem": "\u05DD",
    "f-nun": "\u05DF",
    "f-peh": "\u05E3",
    "f-tsadi": "\u05E5",
}
_ALIASES = {
    "'": "aleph",
    "b": "bet",
    "g": "gimmel",
    "d": "dalet",
    "h": "heh",
    "v": "vav",
    "z": "zayin",
    "ch": "het",
    "t": "tet",
    "y": "yud",
    "k": "kaf",
    "l": "lamed",
    "m": "mem",
    "n": "nun",
    "s": "samekh",
    ".": "ayin",
    "p": "peh",
    "ts": "tsadi",
    "q": "qof",
    "r": "resh",
    "sh": "shin",
    "th": "tav",

    "kF": "f-kaf",
    "mF": "f-mem",
    "nF": "f-nun",
    "pF": "f-peh",
    "tsF": "f-tsadi",
}
_CONS_TRANSLIT = {
    ("aleph",): "'",
    ("bet",): "v",
    ("gimmel",): "g",
    ("dalet",): "d",
    ("heh",): "h",
    ("vav",): "w",
    ("zayin",): "z",
    ("het",): "ch",
    ("tet",): "t",
    ("yud",): "y",
    ("kaf",): "kh",
    ("lamed",): "l",
    ("mem",): "m",
    ("nun",): "n",
    ("samekh",): "s",
    ("ayin",): ".",   #"\u00B7"=dot
    ("peh",): "ph",
    ("tsadi",): "ts",
    ("qof",): "q",
    ("resh",): "r",
    ("shin", "shin-dot"): "sh",
    ("shin", "sin-dot"): "s",
    ("tav",): "th",  # t

    ("bet", "dagesh"): "B",  # b
    ("gimmel", "dagesh"): "G",
    ("dalet", "dagesh"): "D",  # d
    ("heh", "dagesh"): "H",
    ("vav", "dagesh"): "u",
    ("zayin", "dagesh"): "Z",
    ("het", "dagesh"): "Ch",
    ("tet", "dagesh"): "T",
    ("yud", "dagesh"): "Y",
    ("kaf", "dagesh"): "K",  # k
    ("lamed", "dagesh"): "L",
    ("mem", "dagesh"): "M",
    ("nun", "dagesh"): "N",
    ("samekh", "dagesh"): "S",
    ("ayin", "dagesh"): ".",  #"\u00B7"=dot,
    ("peh", "dagesh"): "P",  # p
    ("tsadi", "dagesh"): "Ts",
    ("qof", "dagesh"): "Q",
    ("resh", "dagesh"): "R",
    ("shin", "shin-dot", "dagesh"): "Sh",
    ("shin", "sin-dot", "dagesh"): "S",
    ("tav", "dagesh"): "T",  # t

    ("f-kaf", "dagesh"): "kh",
    ("f-kaf",): "kh",
    ("f-mem",): "m",
    ("f-nun",): "n",
    ("f-peh", "dagesh"): "p",
    ("f-peh",): "ph",
    ("f-tsadi",): "ts",
}
_VOWEL_TRANSLIT = {
    ("sheva",): "'",
    ("hataf-segol",): "e",  # half
    ("hataf-patah",): "a",  # half
    ("hataf-qamats",): "o",  # half
    ("hireq",): "i",  # short
    ("tsere",): "e",  # long
    ("segol",): "e",  # short
    ("patah",): "a",  # short
    ("qamats",): "a",  # long
    ("holam",): "o",  # long
    ("holam-haser",): "o",  # long
    ("qubuts",): "u",  # long
}
_PUNC_TRANSLIT = {
    ("maqaf",): "-",
    ("paseq",): "|",
    ("sof-pasuq",): ":",
    ("nun-hafukha",): "",
}
_TRANSLIT_SUBS = [
    (r"''", "'"),
    (r" '", " "),
    (r"^'", ""),
    (r"iy", "i"),
    (r"iw ", "i "),
    (r"iw$", "i"),
    (r"ay ", "ai "),
    (r"ay$", "ai"),
    (r"cha ", "ach "),
    (r"cha$", "ach"),
    (r"cho ", "och "),
    (r"cho$", "och"),
    (r"wo", "o"),
]
_MAP = {k: v for dct in [_CANTILLATIONS, _NIQQUD, _PUNCTUATION, _CHARS] for k, v in dct.items()}
_IMAP = {v: k for k, v in _MAP.items()}

_CONS_TMAP = {"".join([_MAP[i] for i in k]): v for k, v in _CONS_TRANSLIT.items()}
_VOWEL_TMAP = {"".join([_MAP[i] for i in k]): v for k, v in _VOWEL_TRANSLIT.items()}
_PUNC_TMAP = {"".join([_MAP[i] for i in k]): v for k, v in _PUNC_TRANSLIT.items()}