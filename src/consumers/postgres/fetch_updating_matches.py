from src.connections import get_consumer
from src.database.inserts import insert_matches
from src.preparing import parsing_updating_matches


import json


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

            massege = json.loads(msg.value().decode('utf-8'))
            payload = massege.get('payload')
            
            matches = parsing_updating_matches(payload)

            insert_matches(matches)
            consumer.commit()

    finally:
        consumer.close()




if __name__ == '__main__':
    fetch_updating_matches()