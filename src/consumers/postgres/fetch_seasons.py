from src.connections import get_consumer
from src.database.queries import get_league_id_by_tournaments
from src.database.inserts import insert_seasons
from src.preparing import prepare_seasons

from src.utils import handle_retry

import json






def fetch_seasons():
    """
    правим даты в уже загруженных текущих сезонах и добавляем новые исторические из топика past_seasons
    """


    consumer = get_consumer('fetch_seasons')
    consumer.subscribe(['past_seasons'])

    try:
        # league_ids возвращает id лиги по (tournament_id, tournament_stage_id) текущего сезона
        any_current_seasons = True
        league_ids = get_league_id_by_tournaments(any_current_seasons) 



        while True:
            # получаем message
            msg = consumer.poll(1.0)

            if msg is None:
                continue
            if msg.error():
                print(msg.error())
                continue

            massege = json.loads(msg.value().decode('utf-8'))
            payload = massege.get('payload')
            
            seasons, league_ids = prepare_seasons(payload, league_ids)

            if seasons is None:
                handle_retry(massege, 'past_seasons')
                consumer.commit()
                continue

            insert_seasons(seasons)
            
            consumer.commit()

    finally:
        consumer.close()
        


if __name__ == '__main__':
    fetch_seasons()