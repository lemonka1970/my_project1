from confluent_kafka import Producer, Consumer
from confluent_kafka.admin import NewTopic, AdminClient

from dotenv import load_dotenv
import os
load_dotenv()

def create_topics():
    admin = AdminClient({
        'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS')
    })

    topics = [
        NewTopic("scoreboards", num_partitions=1, replication_factor=1),
        NewTopic("past_seasons", num_partitions=1, replication_factor=1),
        NewTopic("standings", num_partitions=1, replication_factor=1),
        NewTopic("initialize_matches", num_partitions=1, replication_factor=1),
        NewTopic("update_matches", num_partitions=1, replication_factor=1)
    ]

    admin.create_topics(topics)


def get_producer():
    return Producer({
        'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
        'acks': 'all',
        'enable.idempotence': True
    })


def get_consumer(group_id:str):
    return Consumer({
        'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
        'group.id': group_id,
        'auto.offset.reset': 'earliest'
    })




