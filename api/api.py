"""
This is deployed as a lambda function in AWS.
"""
import decimal
from functools import lru_cache
import itertools
import json
from pathlib import Path

import boto3
from boto3.dynamodb.conditions import Key


print("Loading function")
dynamodb = boto3.resource("dynamodb")
bibles_table = dynamodb.Table("B3Bibles")
misc_table = dynamodb.Table("B3Misc")

resources_dir = Path(__file__).parent / "resources"


def handler(event, context):
    """
    Handles all API calls for barebonesbible.com.
    """
    path = event["path"]
    query = event["queryStringParameters"]
    print(f"Received path={path} and query={query}")

    root, *parts = path.strip("/").split("/")
    if root not in {"books", "strongs"}:
        return _response(404, {"message": f"Invalid resource '{root}'"})

    # 1. User has requested /strongs
    if root == "strongs":
        return _response(200, resource("strongs"))
    
    # 2. User has requested /books
    books = resource("books")
    if not parts:
        return _response(200, _books_by_collection(books))
        
    # 3. User has requested /books/{code}
    if len(parts) == 1 and parts[0] in books:
        return _response(200, books[parts[0]])
        
    # 4. User has requested /books/{code}/{start}/{end}
    if len(parts) == 3 and parts[0] in books and is_cv(parts[1]) and is_cv(parts[2]):
        result = {"verses": _fetch_verses(parts)}
        return _response(200, result)
    
    # 5. Failed
    return _response(404, {"message": f"Invalid path: {path}"})


def _fetch_verses(parts):
    code = parts[0]
    c1, v1 = to_cv(parts[1])
    c2, v2 = to_cv(parts[2])
    verses = []
    for c in range(c1, c2 + 1):
        items = chapter(code, c)
        if c == c1:
            items = [item for item in items if item["verseNum"] >= v1]
        if c == c2 and v2:
            items = [item for item in items if item["verseNum"] <= v2]
        verses.extend(items)
    return verses


def _books_by_collection(books_by_code):
    return [
        {
            "collection": collection,
            "books": list(group),
        }
        for collection, group in itertools.groupby(books_by_code.values(), key=lambda x: x["collection"])
    ]


@lru_cache(maxsize=10)
def resource(name):
    """
    Load json resource.
    """
    path = (resources_dir / f"{name}.json")
    with path.open(encoding="utf8") as f:
        return json.load(f)


@lru_cache(maxsize=50)
def chapter(code, chapter_num):
    """
    Load chapter from bibles table
    """
    condition = Key("chapterId").eq(f"{code}.{chapter_num}")
    resp = bibles_table.query(KeyConditionExpression=condition)
    return resp["Items"]
    
    
def is_cv(cv):
    cv = cv.split(".")
    return len(cv) == 2 and cv[0].isdigit() and (cv[1].isdigit() or cv[1] == "x")
    
    
def to_cv(cv):
    c, v = cv.split(".")
    c = int(c)
    v = None if v == "x" else int(v)
    return c, v
    
    
def _response(code, content):
    return {
        "statusCode": str(code),
        "body": json.dumps(content, cls=DecimalEncoder),
        "headers": {
            "Access-Control-Allow-Origin" : "*",
            "Access-Control-Allow-Credentials" : "true",
            "Content-Type": "application/json",
        },
    }
    
    
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return int(o)
        return super().default(o)
