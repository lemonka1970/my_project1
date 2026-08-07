import psycopg2
from psycopg2.extras import execute_values
from confluent_kafka import Producer, Consumer
from minio import Minio

from dotenv import load_dotenv
import os

load_dotenv()




def get_connection():
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_PORT'),
        dbname=os.getenv('POSTGRES_DB'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD')
        )



def get_producer():
    return Producer({
        'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS')
    })


def get_consumer(group_id:str):
    return Consumer({
        'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
        'group.id': group_id,
        'auto.offset.reset': 'earliest'
    })


def get_client():
    return Minio(
        endpoint=os.getenv('S3_ENDPOINT'),
        access_key=os.getenv('S3_ACCESS_KEY'),
        secret_key=os.getenv('S3_SECRET_KEY'),
        secure=False
    )



def main():

    c = 0

if __name__ == '__main__':
    main()
