from src.connections import get_connection, get_consumer

import json
from psycopg2.extras import execute_values



def fetch_regions():
    """
    Из топика scoreboard перебираем json-ы главного табло и сохраняем регионы в postgres
    """

    query = """
                INSERT INTO regions (flashscore_region_id, region_name)
                VALUES %s
                ON CONFLICT (flashscore_region_id)
                DO NOTHING
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

            payload = json.loads(msg.value().decode('utf-8'))
            data = payload.get('scoreboard', [])
            regions = set()


            # выделяем из него регионы и готовим к загрузке
            for el in data:
                if el.get('~ZA') and el.get('ZB'):
                    # ZB: flashscore_region_id
                    # ZY: region_name
                    regions.add((el.get('ZB'), el.get('ZY')))

            if not regions:
                continue

            with get_connection() as conn:
                with conn.cursor() as cur:
                    execute_values(cur, query, list(regions))

            consumer.commit()


    finally:
        consumer.close()


if __name__ == '__main__':
    fetch_regions()