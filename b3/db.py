import logging

import boto3


def upload(records, table):
    """
    Upload records to dynamodb.
    """
    logging.info(f"Uploading {len(records):,} records to {table}")
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table)
    with table.batch_writer() as batch:
        for record in records:
            batch.put_item(Item=record)
    logging.info("Upload complete")
