from src.connections import get_consumer, get_connection
from src.utils import get_teams, get_league_names

import json
from psycopg2.extras import execute_values
from datetime import datetime


def fetch_updating_matches():

    query = """
    INSERT INTO matches (time, flashscore_match_feed, 
                        home_team_id, away_team_id, 
                        home_score, away_score, 
                        home_penalties, away_penalties,
                        status, season_id, league_id)
    VALUES %s
    ON CONFLICT (flashscore_match_feed)
    DO NOTHING
    """

    consumer = get_consumer('fetch_initializetion_matches')
    consumer.subscribe(['initialize_matches'])


    try:

        while True:
            # достаем и проверяем message
            msg = consumer.poll(1.0)

            if msg is None:
                continue
            if msg.error():
                print(msg.error())
                continue

            payload = json.loads(msg.value().decode('utf-8'))
            
            league_id = payload.get('league_id')
            season_id = payload.get('season_id')
            h2h = payload.get('h2h')

            leagues = get_league_names()
            teams = get_teams(league_id)
            matches = set()


            # заглядываем только в первые 2 блока (последние игры домашней и гостевой команд)
            for el in h2h[:104]:
                if '~KC' in el:
                    print(el)
                    match = [
                        el.get('~KC'), # time
                        el.get('KP'), # flashscore_match_feed
                        el.get('UQ'), # home_team
                        el.get('UO'), # away_team
                        el.get('KU'), # home_score
                        el.get('KT'), # away_score
                        el.get('KX'), # home_penalties
                        el.get('KY'), # away_penalties
                        'completed', # status
                        season_id, # season_id
                        el.get('KF') # league_name
                    ]

                    if match[0] is not None:
                        match[0] = datetime.fromtimestamp(int(match[0]))

                    # если вместо имен команд у нас None, то просто пропускаем этот матч
                    match[2] = teams.get(match[2])
                    match[3] = teams.get(match[3])
                    # если лиги еще нет в бд, то пока просто пропускаем этот матч
                    match[10] = leagues.get(match[10])
                    if match[3] is None or match[2] is None or match[10] is None:
                        continue

                    for ind in [4, 5]:  # если счет представляет собой '' '', то заменяем значения на None
                        if match[ind] == '':
                            match[ind] = None


                    matches.add(tuple(match))

            with get_connection() as conn:
                with conn.cursor() as cur:
                    execute_values(cur, query, list(matches))
            consumer.commit()

    finally:
        consumer.close()




if __name__ == '__main__':
    fetch_updating_matches()