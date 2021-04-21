# Bare Bones Bible Backend
Backend stuff for barebonesbible.com, including:
- Scripts to populate the dynamo-db table
- The API code

## Setup
Do the following:
1. Create a virtual environment `python -m venv .venv`
2. Activate it with `source .venv/bin/activate`
3. Install requirements with `pip install -r requirements.txt`
4. Set environment variables for `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` and `AWS_DEFAULT_REGION` - for access to DynamoDB
5. Run the following:
```python
python b3 gather-kjv
python b3 gather-web
python b3 gather-wlc
python b3 gather-gnt
python b3 gather-lxx
```
6. Upload to dynamo db using:
```python
python b3 upload
```