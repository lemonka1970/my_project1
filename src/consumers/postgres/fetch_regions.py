from src.connections import get_consumer
from src.database.inserts import insert_regions
from src.preparing import parsing_regions

import json



def fetch_regions():
    """
    Из топика scoreboard перебираем json-ы главного табло и сохраняем регионы в postgres
    """


    consumer = get_consumer('fetch_region')
    consumer.subscribe(['scoreboards'])

    try:
        while True:
            # вытаскиваем наш json
            msg = consumer.poll(1.0)

            if msg is None:
                continue

            if msg.error():
                print(msg.error())
                continue

            massege = json.loads(msg.value().decode('utf-8'))
            payload = massege.get('payload', [])

            if not payload:
                continue

            # парсим scoreboard на регионы
            regions = parsing_regions(payload)

            if not regions:
                continue

            insert_regions(regions)

            consumer.commit()


    finally:
        consumer.close()


if __name__ == '__main__':
    fetch_regions()