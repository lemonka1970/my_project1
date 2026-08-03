from src.connections import get_connection, get_consumer

import time
import json
from psycopg2.extras import execute_values





def fetch_teams():
    """
    
    """


    query = """
        INSERT INTO teams (team_name, flashscore_team_feed, flashscore_team_url)
        VALUES %s
        ON CONFLICT (flashscore_team_feed)
        DO NOTHING
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

            payload = json.loads(msg.value().decode('utf-8'))
            standings = payload.get('standings', [])

            teams = set()

            for el in standings:
                if el.get('~TR'):
                    teams.add((
                        el.get('TN'), # team_name
                        el.get('TI'), # flashscore_team_feed
                        el.get('TIU') # flashscore_team_url
                        ))

            with get_connection() as conn:
                with conn.cursor() as cur:
                    execute_values(cur, query, list(teams))
            consumer.commit()

    finally:
        consumer.close()



if __name__ == '__main__':
    fetch_teams()