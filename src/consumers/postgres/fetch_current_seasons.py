from src.connections import get_consumer
from src.database.queries import get_league_id_by_flashscore_feed
from src.database.inserts import insert_seasons

import json
import logging
logger = logging.getLogger(__name__)






def prepare_current_seasons(payload, leagues):

    scoreboard = payload.get('scoreboard', [])
    if scoreboard:
        scoreboard = scoreboard[0]
    else:
        return None

    if scoreboard.get('~ZA'):
        
        row = [
            scoreboard.get('ZE'), # tournament_id
            scoreboard.get('ZC'), #  tournament_stage_id
            0, 0, # dates
            True, # is_current
            scoreboard.get('ZEE') # flashscore_league_feed
            ]

        row[5] = leagues.get(row[5])

    return row





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
                logger.error('fetch_current_league: %s', msg.error())
                continue

            payload = json.loads(msg.value().decode('utf-8'))
            if payload == 'message_finally':
                break

            current_seasons = prepare_current_seasons(payload, leagues)
            
            if current_seasons:
                insert_seasons(current_seasons)

            consumer.commit()

    finally:
        consumer.close()



if __name__ == '__main__':
    fetch_current_seasons()