from src.kafka_fn import get_consumer
from src.database.queries import get_region_id_by_flashscore_id
from src.database.inserts import insert_leagues

import json
import logging

logger = logging.getLogger(__name__)





def prepare_leagues(payload, regions):


    keys = [
        'ZEE', # flashscore_league_feed
        'ZD', # competition_type
        'ZG', # stage_type
        'ZJ', # category_id
        'ZL', # league_url
        '~ZA', # league_full_name
        'ZB' # flashcore_region_id
        ]


    scoreboard = payload.get('scoreboard', [])
    if not scoreboard:
        logger.warning("prepare_leagues: scoreboards is empty")
        return None
    scoreboard = scoreboard[0]


    # вылавлинваем из json наши лиги
    # и готовим данные к загрузке в postgres
    row = None
    if scoreboard.get('~ZA'):

        row = [scoreboard.get(key) for key in keys]
        try:
            row[5] = row[5].split(': ')[1]
        except IndexError:
            logger.error("prepare_leagues: %s don't split by ':'", row[5])
            return None
        
        region_id = regions.get(int(row[6]))
        if region_id is None:
            logger.warning("prepare_leagues: region %s not in regions", row[6])
            return None
        
        row[6] = region_id


    return row





def fetch_leagues():
    """
    Из топика scoreboard перебираем json-ы главного табло и сохраняем лиги в postgres
    """

    
    consumer = get_consumer('fetch_leagues')
    consumer.subscribe(['scoreboards'])
    leagues = set()

    try:
        regions = get_region_id_by_flashscore_id()
        if not regions:
            logger.warning("fetch_leagues: dict regions is empty")
            raise

        while True:
            # достаем наш json
            msg = consumer.poll(1.0)

            if msg is None:
                continue
            if msg.error():
                logger.error("fetch_leagues: %s", msg.error())
                continue

            payload = json.loads(msg.value().decode('utf-8'))
            if payload == 'message_finally':
                break

            row = prepare_leagues(payload, regions) 

            if row:
                leagues.add(tuple(row))

            consumer.commit()


    finally:
        consumer.close()  
        if leagues:
            insert_leagues(leagues)



if __name__ == '__main__':
    fetch_leagues()