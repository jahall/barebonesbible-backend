"""
This is deployed as a lambda function in AWS.
"""
import decimal
import itertools
import json

import boto3
from boto3.dynamodb.conditions import Key


print("Loading function")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("B3Bibles")


def lambda_handler(event, context):
    """
    Demonstrates a simple HTTP endpoint using API Gateway. You have full
    access to the request and response payload, including headers and
    status code.

    To scan a DynamoDB table, make a GET request with the TableName as a
    query string parameter. To put, update, or delete an item, make a POST,
    PUT, or DELETE request respectively, passing in the payload to the
    DynamoDB API as a JSON body.
    """
    path = event["path"]
    query = event["queryStringParameters"]
    print(f"Received path={path} and query={query}")

    resource, *parts = path.strip("/").split("/")
    if resource != "books":
        return _response(404, {"message": f"Invalid resource '{resource}'"})
    
    # 1. User has requested /books
    if not parts:
        return _response(200, _BOOKS_BY_COLLECTION)
        
    # 2. User has requested /books/{code}
    if len(parts) == 1 and parts[0] in _BOOKS:
        return _response(200, _BOOKS[parts[0]])
        
    # 3. User has requested /books/{code}/{start}/{end}
    if len(parts) == 3 and parts[0] in _BOOKS and is_cv(parts[1]) and is_cv(parts[2]):
        code = parts[0]
        c1, v1 = to_cv(parts[1])
        c2, v2 = to_cv(parts[2])
        verses = []
        for c in range(c1, c2 + 1):
            condition = Key("chapterId").eq(f"{code}.{c}")
            resp = table.query(KeyConditionExpression=condition)
            items = resp["Items"]
            if c == c1:
                items = [item for item in items if item["verseNum"] >= v1]
            if c == c2 and v2:
                items = [item for item in items if item["verseNum"] <= v2]
            verses.extend(items)
        result = {
            "verses": verses,
        }
        return _response(200, result)
    
    # 4. Failed
    return _response(404, {"message": f"Invalid path: {path}"})
    
    
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
        
        
_BOOKS = [
    ("Torah", "Gen", "Genesis", 50, "Ge,Gn"),
    ("Torah", "Exod", "Exodus", 40, "Ex,Exo"),
    ("Torah", "Lev", "Leviticus", 27, "Le,Lv"),
    ("Torah", "Num", "Numbers", 36, "Nu,Nm,Nb"),
    ("Torah", "Deut", "Deuteronomy", 34, "De,Dt"),
    ("Neviim", "Josh", "Joshua", 24, "Jos,Jsh"),
    ("Neviim", "Judg", "Judges", 21, "Jdg,Jg,Jdgs"),
    ("Neviim", "1Sam", "1 Samuel", 31, "1Sm,1Sa"),
    ("Neviim", "2Sam", "2 Samuel", 24, "2Sm,2Sa"),
    ("Neviim", "1Kgs", "1 Kings", 22, "1Ki,1Kin"),
    ("Neviim", "2Kgs", "2 Kings", 25, "2Ki,2Kin"),
    ("Neviim", "Isa", "Isaiah", 66, "Is"),
    ("Neviim", "Jer", "Jeremiah", 52, "Je,Jr"),
    ("Neviim", "Ezek", "Ezekiel", 48, "Eze,Ezk"),
    ("Neviim", "Hos", "Hosea", 14, "Ho"),
    ("Neviim", "Joel", "Joel", 3, "Jl"),
    ("Neviim", "Amos", "Amos", 9, "Am"),
    ("Neviim", "Obad", "Obadiah", 1, "Ob"),
    ("Neviim", "Jonah", "Jonah", 4, "Jnh,Jon"),
    ("Neviim", "Mic", "Micah", 7, "Mc"),
    ("Neviim", "Nah", "Nahum", 3, "Na"),
    ("Neviim", "Hab", "Habakkuk", 3, "Hb"),
    ("Neviim", "Zeph", "Zephaniah", 3, "Zep,Zp"),
    ("Neviim", "Hag", "Haggai", 2, "Hg"),
    ("Neviim", "Zech", "Zechariah", 14, "Zec,Zc"),
    ("Neviim", "Mal", "Malachi", 4, "Ml"),
    ("Ketuvim", "Ps", "Psalms", 150, "Psa,Pss,Psm,Pslm,Psalm"),
    ("Ketuvim", "Prov", "Proverbs", 31, "Pro,Prv,Pr"),
    ("Ketuvim", "Job", "Job", 42, "Jb"),
    ("Ketuvim", "Song", "Song of Songs", 8, "Sos,So,Songs,Song of Solomon"),
    ("Ketuvim", "Ruth", "Ruth", 4, "Rth,Ru"),
    ("Ketuvim", "Lam", "Lamemntations", 5, "La"),
    ("Ketuvim", "Eccl", "Ecclesiastes", 12, "Ec,Ecc,Eccle"),
    ("Ketuvim", "Esth", "Esther", 10, "Est,Es"),
    ("Ketuvim", "Dan", "Daniel", 12, "Da,Dn"),
    ("Ketuvim", "Ezra", "Ezra", 10, "Ezr,Ez"),
    ("Ketuvim", "Neh", "Nehemiah", 13, "Ne"),
    ("Ketuvim", "1Chr", "1 Chronicles", 29, "1Ch,1Chron"),
    ("Ketuvim", "2Chr", "2 Chronicles", 36, "2Ch,2Chron"),
    ("New Testament", "Matt", "Matthew", 28, "Mt,Mat"),
    ("New Testament", "Mark", "Mark", 16, "Mrk,Mar,Mk,Mr"),
    ("New Testament", "Luke", "Luke", 24, "Luk,Lk"),
    ("New Testament", "John", "John", 21, "Joh,Jhn,Jn"),
    ("New Testament", "Acts", "Acts", 28, "Act,Ac"),
    ("New Testament", "Rom", "Romans", 16, "Ro,Rm"),
    ("New Testament", "1Cor", "1 Corinthians", 16, "1Co"),
    ("New Testament", "2Cor", "2 Corinthians", 13, "2Co"),
    ("New Testament", "Gal", "Galatians", 6, "Ga"),
    ("New Testament", "Eph", "Ephesians", 6, "Ephes"),
    ("New Testament", "Phil", "Philippians", 4, "Php,Pp"),
    ("New Testament", "Col", "Colossians", 4, "Co"),
    ("New Testament", "1Thess", "1 Thessalonians", 5, "1Thes,1Th"),
    ("New Testament", "2Thess", "2 Thessalonians", 3, "2Thes,2Th"),
    ("New Testament", "1Tim", "1 Timothy", 6, "1Ti"),
    ("New Testament", "2Tim", "2 Timothy", 4, "2Ti"),
    ("New Testament", "Titus", "Titus", 3, "Tit"),
    ("New Testament", "Phlm", "Philemon", 1, "Phm,Pm,Philem"),
    ("New Testament", "Heb", "Hebrews", 13, "He"),
    ("New Testament", "Jas", "James", 5, "Jm"),
    ("New Testament", "1Pet", "1 Peter", 5, "1Pe,1Pt"),
    ("New Testament", "2Pet", "2 Peter", 3, "2Pe,2Pt"),
    ("New Testament", "1John", "1 John", 5, "1Jhn,1Joh,1Jn"),
    ("New Testament", "2John", "2 John", 1, "2Jhn,2Joh,2Jn"),
    ("New Testament", "3John", "3 John", 1, "3Jhn,3Joh,3Jn"),
    ("New Testament", "Jude", "Jude", 1, "Jd,Jud"),
    ("New Testament", "Rev", "Revelation", 22, "Re"),
]


_BOOKS = {
    code: {
        "collection": collection,
        "code": code,
        "name": name,
        "chapters": chapters,
        "aliases": [a for a in aliases.split(",")] if aliases else [],
    }
    for collection, code, name, chapters, aliases in _BOOKS
}


_BOOKS_BY_COLLECTION = [
    {
        "collection": collection,
        "books": list(group),
    }
    for collection, group in itertools.groupby(_BOOKS.values(), key=lambda x: x["collection"])
]
