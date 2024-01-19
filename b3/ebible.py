import logging
import zipfile

from .parser.usfx import parse_usfx
from .utils import download, get_cache_path


_ROOT_URL = "https://ebible.org/Scriptures"

_TRANSLATION_FILE_MAP = {
    # English
    "enasv": "eng-asv",  # American Standard Version
    "enkjv": "eng-kjv2006",  # King James Version
    "enlxx": "eng-uk-lxx2012",  # British Septuagint
    #"enWeb": "eng-web",  # World English Bible
    "enweb": "engwebpb",  # World English Bible (British)
    "enwmb": "engwmb",  # World Messianic Bible
    # Greek
    "grlxx": "grcbrent",  # Brenton Septuagint
    "grtisch": "grc-tisch",  # Greek New Testament (Tischendorf)
    "grsbl": "grc_sblgnt",  # Greek New Testament (SBL)
    # Hebrew
    "hemas": "hbo",  # Masoretic
    "hewlc": "hboWLC",  # Westminster Leningrad Codex
}

# USFX and OSIS are common open standards, see diffs here: https://ebible.org/usfx/#differences
# This contains good stuff: https://ebible.org/Scriptures/engwebp_usfx.zip


def fetch_translation_from_ebible(translation):
    """
    Fetch and parse USFX xml-files from ebible.org.
    """
    translation = translation.lower()
    filename = _TRANSLATION_FILE_MAP[translation] + "_usfx"
    logging.info(f"Downloading {filename}.xml")
    path = _download_file(translation, filename)
    records = parse_usfx(path)
    logging.info(f"Parsed {len(records)} verses")
    return records


def _download_file(translation, filename):
    zipurl = f"{_ROOT_URL}/{filename}.zip"
    zippath = get_cache_path("raw", translation, f"{filename}.zip")
    xmlpath = get_cache_path("raw", translation, f"{filename}.xml")

    download(zipurl, zippath)
    if not xmlpath.exists():
        logging.info(f"Unpacking {xmlpath.name}")
        with zipfile.ZipFile(zippath) as z:
            with z.open(xmlpath.name) as xf, xmlpath.open("wb") as f:
                f.write(xf.read())
    return xmlpath