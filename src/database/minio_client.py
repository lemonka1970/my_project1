from minio import Minio

from dotenv import load_dotenv
import os

load_dotenv()
def get_client():
    return Minio(
        endpoint=os.getenv('S3_ENDPOINT'),
        access_key=os.getenv('S3_ACCESS_KEY'),
        secret_key=os.getenv('S3_SECRET_KEY'),
        secure=False
    )