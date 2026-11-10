from src.kafka_fn import get_consumer
from src.database.postgres.inserts import insert_matches
from src.database.postgres.queries import get_team_id_by_feed, get_league_id_by_name


import json
from datetime import datetime
import logging
logger = logging.getLogger(__name__)





def parsing_initializetion_matches(payload, leagues, teams):

    h2h = payload.get('h2h')
    # ВАЖНО: не вынимаем извне лигу, так как внутри json все последние матчи команд, 
    # в том числе проходившие в рамках других лиг
    
    league_matches = set()


    # идем по всем совместным играм
    KB_count = 0
    for el in h2h:
        if el.get('~KB'): # аккуратно выделяем нужные нам игры
            KB_count += 1
        if KB_count == 3: # в третьей секции находятся все очные встречи
            if '~KB' in el.keys():
                continue
            if '~KA' in el.keys():
                break

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
                None, # season_id
                league_full_name # league_name
                ] 

            if match[0] is not None:
                match[0] = datetime.fromtimestamp(int(match[0]))

            # если вместо имен команд у нас None, то просто пропускаем этот матч
            match[2] = teams.get(match[2])
            match[3] = teams.get(match[3])
            # если лиги еще нет в бд, то пока просто пропускаем этот матч
            match[10] = leagues.get(match[10])
            if match[2] is None or match[3] is None or match[10] is None:
                logger.error("initializetion_matches: match %s is not loading", match[1])
                continue

            for ind in [4, 5]: # если счет представляет собой '' '', то заменяем значения на None
                if match[ind] == '':
                    match[ind] = None

            # print(match)
            league_matches.add(tuple(match))

    return league_matches




def fetch_initializetion_matches():

    consumer = get_consumer('fetch_initializetion_matches')
    consumer.subscribe(['initialize_matches'])


    try:
        leagues = get_league_id_by_name()
        teams = get_team_id_by_feed()
        if not leagues:
            logger.error("fetch_initializetion_matches: dict leagues is enpty")
            raise
        if not teams:
            logger.error('fetch_initializetion_matches: dict teams is empty')

        while True:
            # достаем и проверяем message
            msg = consumer.poll(1.0)

            if msg is None:
                continue
            if msg.error():
                logger.error("initializetion_matches: %s", msg.error())
                continue

            payload = json.loads(msg.value().decode('utf-8'))
            # if payload == 'message_finally':
            #     break

            league_matches = parsing_initializetion_matches(payload, leagues, teams)


            if league_matches:
                insert_matches(league_matches)
            consumer.commit()

    finally:
        consumer.close()




if __name__ == '__main__':
    fetch_initializetion_matches()