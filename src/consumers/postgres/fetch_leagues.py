from src.connections import get_connection, get_consumer
from src.utils import get_regions

import time
import json
from psycopg2.extras import execute_values



def fetch_leagues():
    """
    Из топика scoreboard перебираем json-ы главного табло и сохраняем лиги в postgres
    """

    query = """
        INSERT INTO leagues (flashscore_league_feed, competition_type, stage_type, category_id, league_url, league_name,
                region_id)
        VALUES %s
        ON CONFLICT (flashscore_league_feed)
        DO NOTHING
        """

    
    consumer = get_consumer('fetch_leagues')
    consumer.subscribe(['scoreboards'])

    try:

        keys = [
                'ZEE', # flashscore_league_feed
                'ZD', # competition_type
                'ZG', # stage_type
                'ZJ', # category_id
                'ZL', # league_url
                '~ZA', # league_full_name
                'ZB' # flashcore_region_id
                ]
        regions = get_regions()



        while True:
            # достаем наш json
            msg = consumer.poll(1.0)

            if msg is None:
                continue
            if msg.error():
                print(msg.error())
                continue

            payloads = json.loads(msg.value().decode('utf-8'))
            el = payloads.get('scoreboard', [])
            if el:
                el = el[0]
            
            leagues = set()

            # вылавлинваем из json наши лиги
            # и тоговим данные к загрузке в postgres
            if el.get('~ZA'):

                row = [el.get(key) for key in keys]
                row[5] = row[5].split(': ')[1]

                # на случай, если какого-то региона у нас не оказалось
                while True:
                    row[6] = regions.get(int(row[6]))
                    if row[6] is not None:
                        break

                    time.sleep(10)
                    regions = get_regions()


                leagues.add(tuple(row))
                

            with get_connection() as conn:
                with conn.cursor() as cur:
                    execute_values(cur, query, list(leagues))

            consumer.commit()


    finally:
        consumer.close()  



if __name__ == '__main__':
    fetch_leagues()