from src.connections import get_connection, get_consumer
from src.utils import get_leagues

import time
import json
from psycopg2.extras import execute_values






def fetch_current_seasons():
    """
    Из топика scoreboard перебираем json-ы главного табло 
    и сохраняем сырой вариант текущих сезонов в postgres
    """

    consumer = get_consumer('fetch_current_seasons')
    consumer.subscribe(['scoreboards'])

    query = """
    INSERT INTO seasons (tournament_id, tournament_stage_id, start_date, end_date, is_current, league_id)
    VALUES %s
    ON CONFLICT (tournament_id, tournament_stage_id)
    DO UPDATE SET
    is_current = EXCLUDED.is_current
    """

    try:
        leagues = get_leagues()



        while True:
            # достаем message
            msg = consumer.poll(1.0)

            if msg is None:
                continue
            if msg.error():
                print(msg.error())
                continue

            payload = json.loads(msg.value().decode('utf-8'))
            data = payload.get('scoreboard')
            current_seasons = set()

            for el in data:
                if '~ZA' in el.keys():
                    
                    row = [
                        el.get('ZE'), # tournament_id
                        el.get('ZC'), #  tournament_stage_id
                        0, 0, # dates
                        True, # is_current
                        el.get('ZEE') # flashscore_league_feed
                        ]
                    
                    while True:
                        row[5] = leagues.get(row[5])
                        if row[5] is not None:
                            break

                        time.sleep(10)
                        leagues = get_leagues()


                    current_seasons.add(tuple(row))

            with get_connection() as conn:
                with conn.cursor() as cur:
                    execute_values(cur, query, list(current_seasons))

            consumer.commit()

    finally:
        consumer.close()



if __name__ == '__main__':
    fetch_current_seasons()