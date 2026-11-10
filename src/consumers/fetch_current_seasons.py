from src.kafka_fn import get_consumer
from src.database.postgres.queries import get_league_id_by_flashscore_feed
from src.database.postgres.inserts import insert_seasons

import json
import logging
logger = logging.getLogger(__name__)






def prepare_current_seasons(payload, leagues):

    scoreboard = payload.get('scoreboard', [])
    if not scoreboard:
        logger.warning("prepare_current_seasons: scoreboards is empty")
        return None
    scoreboard = scoreboard[0]

    row = None
    # мало ли, что может оказаться первым
    if scoreboard.get('~ZA'):
        
        row = [
            scoreboard.get('ZE'), # tournament_id
            scoreboard.get('ZC'), #  tournament_stage_id
            0, 0, # dates
            True, # is_current
            scoreboard.get('ZEE') # flashscore_league_feed
            ]

        league_id = leagues.get(row[5])
        if league_id is None:
            logger.warning("prepare_current_seasons: league %s not in leagues", row[5])
            return None
        
        row[5] = league_id

    return row





def fetch_current_seasons():
    """
    Из топика scoreboard перебираем json-ы главного табло 
    и сохраняем сырой вариант текущих сезонов в postgres
    """

    consumer = get_consumer('fetch_current_seasons')
    consumer.subscribe(['scoreboards'])
    current_seasons = set()

    try:
        leagues = get_league_id_by_flashscore_feed()
        if not leagues:
            logger.error("fetch_current_leagues: dict leagues is empty")
            raise

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

            row = prepare_current_seasons(payload, leagues)
            
            if row:
                current_seasons.add(tuple(row))

            consumer.commit()

    finally:
        consumer.close()
        if current_seasons:
            insert_seasons(current_seasons)



if __name__ == '__main__':
    fetch_current_seasons()