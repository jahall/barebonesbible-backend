from collections import defaultdict
import json
import logging
import sys

import click

from b3.db import upload
from b3.ebible import fetch_translation_from_ebible
from b3.openscriptures import fetch_translation_from_openscriptures
from b3.utils import get_cache_path


fmt = "%(asctime)s : %(levelname)s : %(message)s"
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format=fmt)


@click.group()
def cli():
    """
    Main click group.
    """

@cli.command("stage")
@click.argument("translations")
def stage(translations):
    """
    Parse USFX file from ebibles.com.
    """
    translations = translations.lower().split(",")
    for tr in translations:
        logging.info(f"STAGING {tr.upper()}")
        if tr in {"hewlc", "grtisch"}:
            records = fetch_translation_from_openscriptures(tr)
        else:
            records = fetch_translation_from_ebible(tr)
        _save_to_staging(records, tr)
    logging.info(f"Done")


@cli.command("upload")
@click.option("--filt", default="Gen.1,Gen.2,Ps.1,Matt.1,Matt.2", help="Limit number of records uploaded to dynamodb.")
def run_upload(filt):
    """
    Upload staged results to dynamodb.
    """
    records = {}
    for version in ["enasv", "enkjv", "enweb", "enwmb", "hewlc", "grtisch"]:
        logging.info(f"Loading {version.upper()} from staging")
        path = get_cache_path("staging", f"{version}.json")
        if not path.exists():
            logging.warning(f"Ignoring {version} since {path} does not exist.")
            continue
        with path.open(encoding="utf8") as f:
            for r in json.load(f):
                key = r["chapterId"], r["verseNum"]
                if key not in records:
                    records[key] = {
                        "chapterId": r["chapterId"],
                        "verseNum": r["verseNum"],
                        "translations": [],
                    }
                records[key][f"translations"].append({
                    "translation": version[2:].upper(),
                    "lan": version[:2],
                    "tokens": r["tokens"],
                })
    records = list(records.values())
    logging.info(f"Uploading {len(records)} records to dynamodb")
    if filt or filt.lower() != "all":
        logging.warning(f"Limiting to {filt} for upload")
        filt = set(filt.split(","))
        records = [r for r in records if r["chapterId"] in filt or r["chapterId"].split(".")[0] in filt]
    upload(records, table="B3Bibles")
    logging.info(f"Done")


def _save_to_staging(records, version):
    path = get_cache_path("staging", f"{version}.json")
    logging.info(f"Saving {len(records)} to {path}")
    with path.open("w", encoding="utf8") as f:
        json.dump(records, f)


cli()  # pylint: disable=no-value-for-parameter
