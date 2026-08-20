from src.connections import get_producer, get_connection
from src.flahscore import get_data, get_response, get_feed_last_match

from datetime import datetime, timedelta
from itertools import combinations

def produce_scoreboards():
    """
    публикуем табло flashscore по датам
    """

    
    producer = get_producer()

    current_date = datetime.now().date()

    try:

        for day in range(-7, 8):

            feed = f'f_1_{day}_3_ru-kz_1'
            data_json = get_data(feed)

            if not data_json:
                continue

            date = current_date + timedelta(days=day)

            groups = []
            current_groups = []

            # делим матчи по лигам
            for el in data_json:

                if el.get('~ZA'):
                    if current_groups:
                        groups.append(current_groups)

                        current_groups = [el]
                else:
                    current_groups.append(el)

            if current_groups:
                groups.append(current_groups)

            # каждую группу публикуем
            for group in groups:

                if group:
                    payload = {
                        'date': str(date), 
                        'scoreboard': group
                        }

                    producer.produce(
                        topic = 'scoreboards', 
                        value = payload
                        )

        
    finally:
        producer.produce(
            topic='scoreboards',
            value='message_finally'
        )
        producer.flush()



def produce_past_seasons():
    """
    публикуем все предыдущие сезоны для каждой текущей
    """

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

                if response is None:
                    continue

                seasons = (
                    response.json()
                    .get('data', {})
                    .get('getTournamentSeasons', {})
                    .get('other', []))

                if not seasons:
                    continue

                    
                payload = {
                    'tournament_id': tournament_id,
                    'tournament_stage_id': tournament_stage_id,
                    'past_seasons': seasons
                    }
                
                producer.produce(
                    topic='past_seasons',
                    value=payload
                    )

    finally:
        producer.produce(
            topic='past_seasons',
            value='message_finally'
        )
        producer.flush()
        conn.close()






def produce_standings():
    """
    публикуем json-ы турнирных таблиц для каждого сезона
    """

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

                payload = {
                        'tournament_id': tournament_id,
                        'tournament_stage_id': tournament_stage_id,
                        'standings': standings
                    }

                producer.produce(
                    topic='standings',
                    value=payload
                )

    finally:
        producer.produce(
            topic='standings',
        value='message_finally'
        )
        producer.flush()
        conn.close()







def produce_initializetion_matches():
    """
    для каждой лиги публикуем все игры
    """

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

                
                # для каждой лиги получаем список url-ов игравших в нем команд
                cur.execute("""
                    SELECT DISTINCT flashscore_team_url
                    FROM teams
                    JOIN season_team_relations USING(team_id)
                    JOIN seasons USING(season_id)
                    WHERE league_id = %s
                    """, (league_id,))
                team_urls = [url[0] for url in cur.fetchall()]


                # для каждой комбинации команд находим feed их последней очной игры
                for url_team_1, url_team_2 in combinations(team_urls, 2):
                    url_team_1 = url_team_1[6:-1].replace('/', '-')
                    url_team_2 = url_team_2[6:-1].replace('/', '-')

                    feed_match = get_feed_last_match(url_team_1, url_team_2)
                    if feed_match is None:
                        continue


                    # print(feed_match)
                    h2h = get_data('df_hh_1_' + feed_match)
                    if h2h is None:
                        continue

                    payload = {
                        'league_id': league_id, 
                        'url_team_1': url_team_1,
                        'url_team_2': url_team_2,
                        'h2h': h2h
                    }

                    producer.produce(
                        topic='initialize_matches',
                        value=payload
                    )

                    

                    
    finally:
        producer.produce(
            topic='initialize_matches',
            value='message_finally'
        )
        producer.flush()
        conn.close()





def produce_updeting_matches():

    conn = get_connection()
    producer = get_producer()

    try:

        with conn.cursor() as cur:

            # словарь league_id: season_id для актуальных сезонов
            cur.execute("""
                SELECT league_id, season_id
                FROM seasons
                WHERE is_current = True
            """)
            seasons = {league_id: season_id for league_id, season_id in cur.fetchall()}

            cur.execute("""
                SELECT league_id 
                FROM leagues
            """)
            leagues = [league_id[0] for league_id in cur.fetchall()]

            
            
            for league_id in leagues:

                # для каждой лиги собираем все url-ы команд текущего сезона
                cur.execute("""
                    SELECT flashscore_team_url
                    FROM teams
                    JOIN season_team_relations USING(team_id)
                    JOIN seasons USING(season_id)
                    WHERE is_current = True AND league_id = %s
                """, (league_id,))
                team_urls = [url[0] for url in cur.fetchall()]

                if not team_urls:
                    continue

                season_id = seasons.get(league_id)

                # формируем пары и находим feed их последней очной встречи
                url_pairs = []
                for i in range(0, len(team_urls), 2):
                    url_pairs.append((team_urls[i], team_urls[(i + 1) % len(team_urls)]))

                for pair in url_pairs:
                    url_team_1 = pair[0][6:-1].replace('/', '-')
                    url_team_2 = pair[1][6:-1].replace('/', '-')

                    feed_match = get_feed_last_match(url_team_1, url_team_2)
                    if feed_match is None:
                        continue


                    h2h = get_data('df_hh_1_' + feed_match)
                    if h2h is None:
                        continue

                    payload = {
                        'league_id': league_id,
                        'season_id': season_id,
                        'url_team_1': url_team_1,
                        'url_team_2': url_team_2,
                        'h2h': h2h
                    }

                    producer.produce(
                        topic='update_matches',
                        value=payload
                    )


    finally:
        producer.produce(
            topic='update_matches',
            value='message_finally'
        )
        producer.flush()
        conn.close()





def main() :
    c = 0
   

if __name__ == '__main__':
    main()