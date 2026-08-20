from src.connections import get_consumer
from src.database.inserts import insert_teams

import json
import logging
logger = logging.getLogger(__name__)







def parsing_teams(payload):

    standings = payload.get('standings', [])
    
    teams = set()

    for el in standings:
        if el.get('~TR'):
            teams.add((
                el.get('TN'), # team_name
                el.get('TI'), # flashscore_team_feed
                el.get('TIU') # flashscore_team_url
                ))

    return teams





def fetch_teams():
    """
    собираем команды по всем сезонам
    """
    
    consumer = get_consumer('fetch_teams')
    consumer.subscribe(['standings'])

    try:

        while True:

            msg = consumer.poll(1.0)

            if msg is None:
                continue
            if msg.error():
                logger.error("fetch_teams: %s", msg.error())
                continue

            payload = json.loads(msg.value().decode('utf-8'))
            if payload == 'message_finally':
                break

            teams = parsing_teams(payload)

            if teams:
                insert_teams(teams)
            consumer.commit()

    finally:
        consumer.close()



if __name__ == '__main__':
    fetch_teams()