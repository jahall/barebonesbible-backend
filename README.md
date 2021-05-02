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
```bash
python b3 stage enasv,enkjv,enweb,enwmb
python b3 stage hewlc
python b3 stage grtisch
```
6. Upload to dynamo db using:
```bash
python b3 upload --filt=all
python b3 upload-books-meta
```
7. Build and package lambda code using:
```bash
python b3 build-api
```
8. Upload resulting `./build/api.zip` to AWS lambda and deploy