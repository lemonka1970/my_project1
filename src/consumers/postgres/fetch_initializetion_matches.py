from src.connections import get_consumer
from src.database.inserts import insert_matches
from src.preparing import parsing_initializetion_matches

import json
from datetime import datetime


def fetch_initializetion_matches():

    consumer = get_consumer('fetch_initializetion_matches')
    consumer.subscribe(['initialize_matches'])


    try:
        while True:
            # достаем и проверяем message
            msg = consumer.poll(1.0)

            if msg is None:
                continue
            if msg.error():
                print(msg.error())
                continue

            massege = json.loads(msg.value().decode('utf-8'))
            payload = massege.get('payload')

            league_matches = parsing_initializetion_matches(payload)

            insert_matches(league_matches)
            consumer.commit()

    finally:
        consumer.close()




if __name__ == '__main__':
    fetch_initializetion_matches()