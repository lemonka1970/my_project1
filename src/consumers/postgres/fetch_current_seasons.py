from src.connections import get_consumer
from src.database.queries import get_league_id_by_flashscore_feed
from src.database.inserts import insert_seasons
from src.preparing import prepare_current_seasons
from src.utils import handle_retry

import time
import json






def fetch_current_seasons():
    """
    Из топика scoreboard перебираем json-ы главного табло 
    и сохраняем сырой вариант текущих сезонов в postgres
    """

    consumer = get_consumer('fetch_current_seasons')
    consumer.subscribe(['scoreboards'])

    try:
        leagues = get_league_id_by_flashscore_feed()

        while True:
            # достаем message
            msg = consumer.poll(1.0)

            if msg is None:
                continue
            if msg.error():
                print(msg.error())
                continue

            massege = json.loads(msg.value().decode('utf-8'))
            payload = massege.get('payload')

            current_seasons, leagues = prepare_current_seasons(payload, leagues)

            if current_seasons is None:
                handle_retry(massege, 'scoreboard')
                consumer.commit()
                continue

            insert_seasons(current_seasons)

            consumer.commit()

    finally:
        consumer.close()



if __name__ == '__main__':
    fetch_current_seasons()