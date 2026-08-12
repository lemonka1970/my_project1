from src.connections import get_consumer
from src.database.queries import get_region_id_by_flashscore_id
from src.database.inserts import insert_leagues
from src.preparing import prepare_leagues

import time
import json



def fetch_leagues():
    """
    Из топика scoreboard перебираем json-ы главного табло и сохраняем лиги в postgres
    """

    
    consumer = get_consumer('fetch_leagues')
    consumer.subscribe(['scoreboards'])

    try:
        regions = get_region_id_by_flashscore_id()

        while True:
            # достаем наш json
            msg = consumer.poll(1.0)

            if msg is None:
                continue
            if msg.error():
                print(msg.error())
                continue

            payload = json.loads(msg.value().decode('utf-8'))

            # одновременно обновляем regions 
            leagues, regions = prepare_leagues(payload, regions)

            insert_leagues(leagues)

            consumer.commit()


    finally:
        consumer.close()  



if __name__ == '__main__':
    fetch_leagues()