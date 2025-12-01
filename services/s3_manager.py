import json
import boto3
import botocore
import time
from botocore.exceptions import ClientError
from os import getenv

# Load env vars if available (python-dotenv can be used in app)
S3_BUCKET = getenv("S3_BUCKET_NAME")
AWS_REGION = getenv("AWS_REGION", "us-east-1")
BOOKINGS_KEY = getenv("BOOKINGS_KEY", "bookings.json")

s3 = boto3.client("s3", region_name=AWS_REGION)

def _ensure_bucket_exists(bucket):
    try:
        s3.head_bucket(Bucket=bucket)
        return True
    except ClientError as e:
        # Not found or access denied
        raise

def _get_object(bucket, key):
    try:
        resp = s3.get_object(Bucket=bucket, Key=key)
        return resp["Body"].read().decode("utf-8")
    except s3.exceptions.NoSuchKey:
        return None
    except ClientError as e:
        # For other errors re-raise
        raise

def _put_object(bucket, key, data):
    s3.put_object(Bucket=bucket, Key=key, Body=data.encode("utf-8"))

def get_all_bookings():
    """
    Returns list of booking dicts.
    If object not present, returns empty list.
    """
    _ensure_bucket_exists(S3_BUCKET)
    content = _get_object(S3_BUCKET, BOOKINGS_KEY)
    if not content:
        return []
    try:
        doc = json.loads(content)
        return doc.get("bookings", [])
    except json.JSONDecodeError:
        # If file corrupted, return empty
        return []

def save_all_bookings(bookings):
    """
    Overwrites bookings file in S3.
    bookings: list of dicts
    """
    _ensure_bucket_exists(S3_BUCKET)
    payload = {"bookings": bookings}
    _put_object(S3_BUCKET, BOOKINGS_KEY, json.dumps(payload, indent=2))
    return True

def add_booking(booking_dict):
    """
    Adds a booking (dict) to S3-backed list.
    """
    for _ in range(3):  # retry a few times for robustness
        try:
            bookings = get_all_bookings()
            bookings.append(booking_dict)
            save_all_bookings(bookings)
            return booking_dict
        except ClientError as e:
            time.sleep(1)
            last_exc = e
    raise last_exc

def get_booking(booking_id):
    bookings = get_all_bookings()
    for b in bookings:
        if b.get("id") == booking_id:
            return b
    return None

def update_booking(booking_id, updated_fields):
    """
    updated_fields: dict of fields to update
    """
    bookings = get_all_bookings()
    updated = False
    for i, b in enumerate(bookings):
        if b.get("id") == booking_id:
            bookings[i].update(updated_fields)
            updated = True
            break
    if not updated:
        return None
    save_all_bookings(bookings)
    return bookings[i]

def delete_booking(booking_id):
    bookings = get_all_bookings()
    new_bookings = [b for b in bookings if b.get("id") != booking_id]
    if len(new_bookings) == len(bookings):
        # nothing deleted
        return False
    save_all_bookings(new_bookings)
    return True
