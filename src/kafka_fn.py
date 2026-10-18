from confluent_kafka import Producer, Consumer, KafkaError, KafkaException
from confluent_kafka.admin import NewTopic, AdminClient

from dotenv import load_dotenv
import os
load_dotenv()

import logging
logger = logging.getLogger(__name__)

num_partitions_scoreboards = 1
num_partitions_past_seasons = 1
num_partitions_standings = 1
num_partitions_initialize_matches = 1
num_partitions_update_matches = 1

def create_topics():
    admin = AdminClient({
        'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS')
    })

    topics = [
        NewTopic("scoreboards", num_partitions=num_partitions_scoreboards, replication_factor=1),
        NewTopic("past_seasons", num_partitions=num_partitions_past_seasons, replication_factor=1),
        NewTopic("standings", num_partitions=num_partitions_standings, replication_factor=1),
        NewTopic("initialize_matches", num_partitions=num_partitions_initialize_matches, replication_factor=1),
        NewTopic("update_matches", num_partitions=num_partitions_update_matches, replication_factor=1)
    ]

    futures = admin.create_topics(topics)

    for topic, future in futures.items():
        try:
            future.result()
        except KafkaException as e:
            if e.args[0].code() == KafkaError.TOPIC_ALREADY_EXISTS:
                continue
            else:
                logger.error("create_topics: error creating topic '%s': %s", topic, e)
                raise


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




