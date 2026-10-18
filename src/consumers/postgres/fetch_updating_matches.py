from src.kafka_fn import get_consumer
from src.database.inserts import insert_matches
from src.database.queries import get_team_id_by_feed, get_league_id_by_name


import json
from datetime import datetime
import logging
logger = logging.getLogger('__name__')




def parsing_updating_matches(payload, leagues, teams):

    season_id = payload.get('season_id')
    h2h = payload.get('h2h')
    # ВАЖНО: не вынимаем извне лигу, так как внутри json все последние матчи команд, 
    # в том числе проходившие в рамках других лиг

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
        teams = get_team_id_by_feed()
        if not leagues: 
            logger.error("fetch_updating_matches: dict leagues is empty")
            raise
        if not teams:
            logger.error('fetch_updating_matches: dict teams is empty')
            raise

        while True:

            # достаем и проверяем message
            msg = consumer.poll(1.0)

            if msg is None:
                continue
            if msg.error():
                logger.error("updating_matches: %s", msg.error())
                continue

            payload = json.loads(msg.value().decode('utf-8'))
            # if payload == 'message_finally':
            #     break
            
            matches = parsing_updating_matches(payload, leagues, teams)

            if matches:
                insert_matches(matches)
            consumer.commit()

    finally:
        consumer.close()




if __name__ == '__main__':
    fetch_updating_matches()