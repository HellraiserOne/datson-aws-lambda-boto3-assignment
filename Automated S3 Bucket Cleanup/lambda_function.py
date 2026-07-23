import boto3
import os
from datetime import datetime, timezone, timedelta

s3 = boto3.client('s3')

BUCKET_NAME = os.environ.get('BUCKET_NAME', 'datson-lambda-cleanup-test')
# For testing: set AGE_THRESHOLD_MINUTES env var, e.g. 2
# For production: leave unset, defaults to 30 days
AGE_THRESHOLD_MINUTES = os.environ.get('AGE_THRESHOLD_MINUTES')

def lambda_handler(event, context):
    if AGE_THRESHOLD_MINUTES:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=int(AGE_THRESHOLD_MINUTES))
    else:
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)

    deleted_objects = []
    paginator = s3.get_paginator('list_objects_v2')

    for page in paginator.paginate(Bucket=BUCKET_NAME):
        if 'Contents' not in page:
            continue
        for obj in page['Contents']:
            if obj['LastModified'] < cutoff:
                s3.delete_object(Bucket=BUCKET_NAME, Key=obj['Key'])
                deleted_objects.append(obj['Key'])
                print(f"Deleted: {obj['Key']} (LastModified: {obj['LastModified']})")

    print(f"Total objects deleted: {len(deleted_objects)}")
    print(f"Deleted objects: {deleted_objects}")

    return {
        'statusCode': 200,
        'deleted_count': len(deleted_objects),
        'deleted_objects': deleted_objects
    }
