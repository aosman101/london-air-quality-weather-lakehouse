from __future__ import annotations
import os
import json
import boto3

def s3_client():
    return boto3.client(
        "s3",
        endpoint_url=os.getenv("MINIO_ENDPOINT"),
        aws_access_key_id=os.getenv("MINIO_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("MINIO_SECRET_KEY"),
        region_name="us-east-1",
    )

def put_json(bucket: str, key: str, payload: dict) -> None:
    """
    Writes a JSON object to the lake as an object like:
      raw/openaq/YYYY/MM/DD/...json
    """
    s3 = s3_client()
    s3.put_object(Bucket=bucket, Key=key, Body=json.dumps(payload).encode("utf-8"))
