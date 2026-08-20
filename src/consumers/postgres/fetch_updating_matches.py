from src.connections import get_consumer, get_connection
from src.database.inserts import insert_matches
from src.database.queries import get_team_id_by_feed, get_league_id_by_name


import json
from datetime import datetime
import logging
logger = logging.getLogger('__name__')




def parsing_updating_matches(payload, leagues, cur):

    league_id = payload.get('league_id')
    season_id = payload.get('season_id')
    h2h = payload.get('h2h')

    teams = get_team_id_by_feed(league_id, cur)
    matches = set()


    # заглядываем только в первые 2 блока (последние игры домашней и гостевой команд)
    for el in h2h[:104]:
        if '~KC' in el:

            kh, kf = el.get('KH'), el.get('KF')
            league_full_name = kh + ': ' + kf if kh and kf else None
            match = [
                el.get('~KC'), # time
                el.get('KP'), # flashscore_match_feed
                el.get('UQ'), # home_team_feed
                el.get('UO'), # away_team_feed
                el.get('KU'), # home_score
                el.get('KT'), # away_score
                el.get('KX'), # home_penalties
                el.get('KY'), # away_penalties
                'completed', # status
                season_id, # season_id
                league_full_name # full_league_name
            ]

            if match[0] is not None:
                match[0] = datetime.fromtimestamp(int(match[0]))

            # если вместо имен команд у нас None, то просто пропускаем этот матч
            match[2] = teams.get(match[2])
            match[3] = teams.get(match[3])
            # если лиги еще нет в бд, то пока просто пропускаем этот матч
            match[10] = leagues.get(match[10])
            if match[3] is None or match[2] is None or match[10] is None:
                logger.error("updating_matches: match %s is not loading", match[1])
                continue

            for ind in [4, 5]:  # если счет представляет собой '' '', то заменяем значения на None
                if match[ind] == '':
                    match[ind] = None


            matches.add(tuple(match))

    return matches






def fetch_updating_matches():


    consumer = get_consumer('fetch_updating_matches')
    consumer.subscribe(['update_matches'])


    try:
        leagues = get_league_id_by_name()

        with get_connection() as conn:
            with conn.cursor() as cur:

                while True:

                    # достаем и проверяем message
                    msg = consumer.poll(1.0)

                    if msg is None:
                        continue
                    if msg.error():
                        logger.error("updating_matches: %s", msg.error())
                        continue

                    payload = json.loads(msg.value().decode('utf-8'))
                    if payload == 'message_finally':
                        break
                    
                    matches = parsing_updating_matches(payload, leagues, cur)

                    if matches:
                        insert_matches(matches)
                    consumer.commit()

    finally:
        consumer.close()




if __name__ == '__main__':
    fetch_updating_matches()