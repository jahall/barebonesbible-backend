import logging
import sys

import click

from b3.db import upload
from b3.english import fetch_english
from b3.hebrew import fetch_hebrew


fmt = "%(asctime)s : %(levelname)s : %(message)s"
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format=fmt)


@click.group()
def cli():
    """
    Main click group.
    """


@cli.command("populate-english")
@click.option("--translation", default="WEB", help="Which translation to use.")
@click.option("--limit", default=31, help="Limit number of records uploaded to dynamodb.")
def run_populate_english(translation, limit):
    """
    Parse openscriptures xml-files and make my own json ones, then upload to dynamodb.
    """
    records = fetch_english(translation, limit)
    upload(records, table="B3Bibles")


@cli.command("populate-hebrew")
@click.option("--limit", default=31, help="Limit number of records uploaded to dynamodb.")
def run_populate_hebrew(limit):
    """
    Parse openscriptures xml-files and make my own json ones, then upload to dynamodb.
    """
    records = fetch_hebrew(limit)
    upload(records, table="B3Bibles")


cli()  # pylint: disable=no-value-for-parameter
