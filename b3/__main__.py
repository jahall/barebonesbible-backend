from collections import defaultdict
import json
import logging
import sys

import click

from b3.db import upload
from b3.english import fetch_english
from b3.english_annotated import fetch_english_annotated
from b3.hebrew import fetch_hebrew
from b3.utils import get_cache_path


fmt = "%(asctime)s : %(levelname)s : %(message)s"
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format=fmt)


@click.group()
def cli():
    """
    Main click group.
    """

@cli.command("stage")
@click.argument("translation")
def stage(translation):
    """
    Parse USFX file from ebibles.com.
    """
    translation = translation.lower()
    if translation == "wlc":
        records = fetch_hebrew()
    else:
        records = fetch_english_annotated(translation)
    _save_to_staging(records, translation)


@cli.command("upload")
@click.option("--limit", default=31, help="Limit number of records uploaded to dynamodb.")
def run_upload(limit):
    """
    Upload staged results to dynamodb.
    """
    records = {}
    for version in ["kjv", "web", "wmb", "wlc", "gnt", "lxx"]:
        logging.info(f"Loading {version.upper()} from staging")
        path = get_cache_path("staging", f"{version}.json")
        if not path.exists():
            logging.warning(f"Ignoring {version} since {path} does not exist.")
            continue
        with path.open(encoding="utf8") as f:
            for r in json.load(f):
                key = r["chapterId"], r["verseNum"]
                if key not in records:
                    records[key] = {"chapterId": r["chapterId"], "verseNum": r["verseNum"]}
                records[key][f"{version}Tokens"] = r["tokens"]
    records = list(records.values())
    logging.info(f"Uploading {len(records)} records to dynamodb")
    if len(records) > limit:
        logging.warning(f"Limiting to {limit} for upload")
        records = records[:limit]
    upload(records, table="B3Bibles")
    logging.info(f"Done")


def _save_to_staging(records, version):
    path = get_cache_path("staging", f"{version}.json")
    logging.info(f"Saving {len(records)} to {path}")
    with path.open("w", encoding="utf8") as f:
        json.dump(records, f)
    logging.info(f"Done")


cli()  # pylint: disable=no-value-for-parameter
