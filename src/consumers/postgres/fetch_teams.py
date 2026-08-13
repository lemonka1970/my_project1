from src.connections import get_consumer
from src.database.inserts import insert_teams
from src.preparing import parsing_teams

import json





def fetch_teams():
    """
    
    """
    
    consumer = get_consumer('fetch_teams')
    consumer.subscribe(['standings'])

    try:

        while True:

            msg = consumer.poll(1.0)

            if msg is None:
                continue
            if msg.error():
                print(msg.error())
                continue

            massege = json.loads(msg.value().decode('utf-8'))
            payload = massege.get('payload')

            teams = parsing_teams(payload)
            if not teams:
                continue

            insert_teams(teams)
            consumer.commit()

    finally:
        consumer.close()



if __name__ == '__main__':
    fetch_teams()