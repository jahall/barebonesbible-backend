# Bare Bones Bible Backend
Backend stuff for barebonesbible.com, including:
- Scripts to populate the dynamo-db table
- The API code

## Setup
Do the following:
1. Create a virtual environment `python -m venv .venv`
2. Activate it with `source .venv/bin/activate`
3. Upgrade pip with `pip install --upgrade pip`
4. Install requirements with `pip install -r requirements.txt`
5. Set environment variables for `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` and `AWS_DEFAULT_REGION` - for access to DynamoDB
6. Run the following:
```bash
python b3 stage enasv,enkjv,enweb,enwmb
python b3 stage hewlc
python b3 stage grtisch
```
7. Upload to dynamo db using (takes around 25 mins for all bibles)
```bash
python b3 upload-bibles --filt=all
python b3 upload-search
```
8. Build and package lambda code using:
```bash
python b3 build-api
```
9. Upload resulting `./build/api.zip` to AWS lambda and deploy