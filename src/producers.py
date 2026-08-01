from connections import get_producer, get_consumer, get_connection
from flahscore import get_data, get_response
from datetime import datetime, timedelta

import json
from itertools import combinations


def produce_scoreboard():

    
    producer = get_producer()

    current_date = datetime.now().date()

    try:

        for day in range(-7, 8):

            feed = f'f_1_{day}_3_ru-kz_1'
            data_json = get_data(feed)

            if not data_json:
                continue

            date = current_date + timedelta(days=day)
            payload = json.dumps({
                'date': str(date), 
                'data': data_json
                }).encode('utf-8')

            producer.produce(
                topic = 'scoreboards', 
                value = payload
                )

        
    finally:
        producer.flush()



def produce_past_seasons():

    producer = get_producer()

    conn = get_connection()

    try:


        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT tournament_id, tournament_stage_id
                FROM seasons
                WHERE is_current = True
            """)

            for tournament_id, tournament_stage_id in cur.fetchall():

                url = f'https://2.ds.lsapp.eu/pq_graphql?_hash=lph&tournamentId={tournament_id}&tournamentStageId={tournament_stage_id}&projectId=2'
                response = get_response(url)

                seasons = (
                    response.json()
                    .get('data', {})
                    .get('getTournamentSeasons', {})
                    .get('other', []))

                if not seasons:
                    continue

                payload = json.dumps({
                    'feed_season': f'to_{tournament_id}_{tournament_stage_id}_1',
                    'seasons': seasons
                    }).encode('utf-8')
                producer.produce(
                    topic='past_seasons',
                    value=payload
                    )

    finally:
        conn.close()
        producer.flush()





def produce_standings():

    producer = get_producer()
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT tournament_id, tournament_stage_id
                FROM seasons
            """)

            for tournament_id, tournament_stage_id in cur.fetchall():

                feed = f'to_{tournament_id}_{tournament_stage_id}_1'
                standings = get_data(feed)

                if not standings:
                    continue

                payload = json.dumps({
                        'feed_season': feed,
                        'standings': standings
                    }).encode('utf-8')

                producer.produce(
                    topic='standings',
                    value=payload
                )

    finally:
        conn.close()
        producer.flush()






def produce_match_event_ids():

    producer = get_producer()
    conn = get_connection()

    try:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT league_id
                FROM leagues
            """)
            leagues = [league_id[0] for league_id in cur.fetchall()]


            for league_id in leagues:

                cur.execute("""
                    SELECT DISTINCT flashscore_team_url
                    FROM teams
                    JOIN season_team_relations USING(team_id)
                    JOIN seasons USING(season_id)
                    WHERE league_id = %s
                """, (league_id, ))

                team_urls = [team_url[0] for team_url in cur.fetchall()]

                match_feeds = set()

                for url_team_1, url_team_2 in combinations(team_urls, 2):
                    url_team_1 = url_team_1[6:-1].replace('/', '-')
                    url_team_2 = url_team_2[6:-1].replace('/', '-')

                    url = f'https://www.flashscore.com/match/football/{url_team_1}/{url_team_2}/?'
                    response = get_response(url)


                    # максимально топорно достаем feed игры
                    data = response.text.split('<script>\n    ')
                    feed_match = None
                    for el in data:
                        if 'window.environment = {"event_id_c":' in el:
                            feed_match = el[36:44]
                            break
                    if feed_match is None:
                        continue

                    match_feeds.add(feed_match)

                if not match_feeds:
                    continue

                payload = json.dumps({
                    'league_id': league_id,
                    'match_event_ids': list(match_feeds)
                    }).encode('utf-8')
                
                producer.produce(
                    topic='match_event_ids',
                    value=payload
                )
        
    finally:
        conn.close()
        producer.flush()




# def produce_h2h_matches():

#     producer = get_producer()
#     consumer = get_consumer('producer_h2h')
#     conn = get_connection()

#     try:
        
