from src.kafka_fn import get_producer
from src.database.postgres_conn import db_pool
from src.flahscore import get_data, get_feed_last_match

from itertools import combinations
import json
import logging

logger = logging.getLogger(__name__)

from dotenv import load_dotenv
import os
import ast
load_dotenv()
current_league_urls = ast.literal_eval(os.getenv('CURRENT_LEAGUE_URLS'))



def produce_initializetion_matches():
    """
    для каждой лиги публикуем все игры
    """

    producer = get_producer()
    conn = db_pool.getconn()

    try:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT league_id
                FROM leagues
                WHERE league_url IN %s
                """, (current_league_urls,))
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

                logger.info("len team_urls: %s", len(team_urls))


                # для каждой комбинации команд находим feed их последней очной игры
                for url_team_1, url_team_2 in combinations(team_urls, 2):

                    logger.info("Processing pair: %s and %s", url_team_1, url_team_2)

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
                        value=json.dumps(payload).encode('utf-8')
                    )

                logger.info("league %s processing finished", league_id)

    except Exception as e:
            logger.error('produce_updating_matches: %s', (e,))

                    
    # finally:
    #     producer.produce(
    #         topic='initialize_matches',
    #         value=json.dumps('message_finally').encode('utf-8')
    #     )
    #     producer.flush()
    #     db_pool.putconn(conn)





def produce_updeting_matches():

    conn = db_pool.getconn()
    producer = get_producer()

    try:

        with conn.cursor() as cur:

            # словарь league_id: season_id для актуальных сезонов
            cur.execute("""
                SELECT league_id, season_id
                FROM seasons
                JOIN leagues USING(league_id)
                WHERE is_current = True
                AND league_url IN %s
            """, (current_league_urls,))
            seasons = {league_id: season_id for league_id, season_id in cur.fetchall()}

            cur.execute("""
                SELECT league_id 
                FROM leagues
                JOIN leagues USING(league_id)
                WHERE league_url IN %s
            """, (current_league_urls,))
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
                        value=json.dumps(payload).encode('utf-8')
                    )
                    producer.flush()

    except Exception as e:
        logger.error('produce_updating_matches: %s', (e,))

    # finally:
    #     producer.produce(
    #         topic='update_matches',
    #         value=json.dumps('message_finally').encode('utf-8')
    #     )
    #     producer.flush()
    #     db_pool.putconn(conn)


def main():
    c = 0


if __name__ == "__main__":
    main()