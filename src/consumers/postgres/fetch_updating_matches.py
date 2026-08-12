from src.connections import get_consumer
from src.database.inserts import insert_matches
from src.database.queries import get_league_id_by_name
from src.preparing import parsing_updating_matches


import json
from psycopg2.extras import execute_values
from datetime import datetime


def fetch_updating_matches():


    consumer = get_consumer('fetch_updating_matches')
    consumer.subscribe(['update_matches'])


    try:

        while True:

            # достаем и проверяем message
            msg = consumer.poll(1.0)

            if msg is None:
                continue
            if msg.error():
                print(msg.error())
                continue

            payload = json.loads(msg.value().decode('utf-8'))
            
            matches = parsing_updating_matches(payload)

            insert_matches(matches)
            consumer.commit()

    finally:
        consumer.close()




if __name__ == '__main__':
    fetch_updating_matches()