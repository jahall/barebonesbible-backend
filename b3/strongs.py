from collections import defaultdict
import json
import logging
import re
import unicodedata

from .translit import transliterate_greek, transliterate_hebrew
from .utils import download, get_cache_path


_STRONGS_OS_URL = "https://raw.githubusercontent.com/openscriptures/strongs/master/{lan}/strongs-{lan}-dictionary.js"


def fetch_strongs_from_openscriptures():
    """
    Parse openscriptures xml-files and make my own json ones, then upload to dynamodb.
    """
    record = {}
    for lan in ["hebrew", "greek"]:
        logging.info(f"Working on {lan}")
        blob = _download(lan)
        logging.info("...conforming")
        _conform(lan, blob)
        logging.info("...counting")
        _add_counts(lan, blob)
        record[lan] = blob
    return record


def _download(lan):
    """
    Download js files from openscriptures and hack into simple json files.
    """
    url = _STRONGS_OS_URL.format(lan=lan)
    path = get_cache_path("raw", "strongs", f"{lan}.js")
    download(url, path)
    with path.open(encoding="utf8") as f:
        json_str = ""
        write = False
        for line in f:
            if line.startswith("var"):
                json_str = line.split("=", 1)[-1].strip()
                write = True
            elif line.startswith("};"):
                json_str += "}"
                write = False
            elif write:
                # Hacky bespoke nonsense
                line = re.sub(r";\s+module\.exports\s+=.*$", "", line.strip())
                json_str += line
        blob = json.loads(json_str)
    path = path.parent / f"{lan}.json"
    with path.open("w", encoding="utf8") as f:
        json.dump(blob, f)
    return blob


def _conform(lan, blob):
    """
    Alter openscriptures stuff a bit e.g. by adding our own tlit. So end up with these fields:
        - lemma: the word itself
        - def: Strongs definition
        - kjv: KJV definition
        - deriv: derivation
        - tlit: my transliteration
        - pron: openscriptures transliteration
    """
    tlit_func = {
        "greek": transliterate_greek,
        "hebrew": transliterate_hebrew,
    }[lan]
    for v in blob.values():
        v["def"] = v.pop("strongs_def", "")
        v["kjv"] = v.pop("kjv_def", "")
        v["deriv"] = v.pop("derivation", "")
        v["tlit"] = tlit_func(v["lemma"])
        if "translit" in v:
            v["pron"] = v.pop("translit")
        v.pop("xlit", None)


def _add_counts(lan, blob):
    """
    Add reference counts and first occurrences.
    """
    translation = {"greek": "grtisch", "hebrew": "hewlc"}[lan]
    path = get_cache_path("staging", f"{translation}.json")
    if not path.exists():
        raise RuntimeError(f"Make sure you've run `python b3 stage {translation}`")
    counts = defaultdict(int)
    first_refs = defaultdict(list)
    with path.open(encoding="utf8") as f:
        for record in json.load(f):
            ref = f"{record['chapterId']}.{record['verseNum']}"
            for token in record["tokens"]:
                for id_ in token.get("strongs", []):
                    counts[id_] += 1
                    refs = first_refs[id_]
                    if len(refs) == 0 or (len(refs) < 5 and refs[-1] != ref):
                        first_refs[id_].append(ref)
    for id_, v in blob.items():
        v["count"] = counts[id_]
        v["refs"] = first_refs[id_]

