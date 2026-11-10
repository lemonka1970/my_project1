from src.kafka_fn import get_consumer
from src.database.postgres.inserts import insert_regions

import json
import logging

logger = logging.getLogger(__name__)






def parsing_regions(payload):


    scoreboard = payload.get('scoreboard', [])
    if not scoreboard:
        logger.warning("parsing_regions: scoreboards is empty")
        return None
    scoreboard = scoreboard[0]

    row = None
    # выделяем из него регионы и готовим к загрузке
    if scoreboard.get('~ZA') and scoreboard.get('ZB'):
        row = [
            scoreboard.get('ZB'), # flashscore_region_id
            scoreboard.get('ZY') # region_name
        ]
        
    return row




def fetch_regions():
    """
    Из топика scoreboard перебираем json-ы главного табло и сохраняем регионы в postgres
    """


    consumer = get_consumer('fetch_region')
    consumer.subscribe(['scoreboards'])
    regions = set()


    try:
        while True:
            # вытаскиваем наш json
            msg = consumer.poll(1.0)

            if msg is None:
                continue

            if msg.error():
                logger.error('fetch_regions: %s', msg.error())
                continue

            payload = json.loads(msg.value().decode('utf-8'))

            if payload == 'message_finally':
                break

            # парсим scoreboard на регионы
            row = parsing_regions(payload)
            
            if row:
                regions.add(tuple(row))

            consumer.commit()


    finally:
        consumer.close()
        if regions:
            insert_regions(regions)


if __name__ == '__main__':
    fetch_regions()

