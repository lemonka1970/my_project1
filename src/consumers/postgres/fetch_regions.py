from src.connections import get_consumer
from src.database.inserts import insert_regions
from src.preparing import parsing_regions

import json
import logging

logger = logging.getLogger(__name__)






def parsing_regions(payload):
    regions = set()

    scoreboard = payload.get('scoreboard', [])
    if scoreboard:
        scoreboard = scoreboard[0]
    else:
        return None
        
    # выделяем из него регионы и готовим к загрузке
    if scoreboard.get('~ZA') and scoreboard.get('ZB'):
        regions.add((
            scoreboard.get('ZB'), # flashscore_region_id
            scoreboard.get('ZY') # region_name
            ))
        
    return regions




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
                logger.error('fetch_regions: %s', msg.error())
                continue

            payload = json.loads(msg.value().decode('utf-8'))

            if payload == 'message_finally':
                break

            # парсим scoreboard на регионы
            regions = parsing_regions(payload)
            
            if regions:
                insert_regions(regions)

            consumer.commit()


    finally:
        consumer.close()


if __name__ == '__main__':
    fetch_regions()