from src.kafka_fn import get_producer
from src.database.postgres_conn import db_pool
from src.flahscore import get_data, get_response

from datetime import datetime, timedelta
import json





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
                        value = json.dumps(payload).encode('utf-8')
                        )

        
    finally:
        producer.produce(
            topic='scoreboards',
            value=json.dumps('message_finally').encode('utf-8')
        )
        producer.flush()




def produce_past_seasons():
    """
    публикуем все предыдущие сезоны для каждой текущей
    """

    producer = get_producer()

    conn = db_pool.getconn()

    try:

        with conn.cursor() as cur:

            
            cur.execute("""
                SELECT DISTINCT league_id, tournament_id, tournament_stage_id
                FROM seasons
                WHERE is_current = True
            """)

            for league_id, tournament_id, tournament_stage_id in cur.fetchall():

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
                    'league_id': league_id,
                    'tournament_id': tournament_id,
                    'tournament_stage_id': tournament_stage_id,
                    'past_seasons': seasons
                    }
                
                producer.produce(
                    topic='past_seasons',
                    value=json.dumps(payload).encode('utf-8')
                    )

    finally:
        producer.produce(
            topic='past_seasons',
            value=json.dumps('message_finally').encode('utf-8')
        )
        producer.flush()
        db_pool.putconn(conn)






def produce_standings():
    """
    публикуем json-ы турнирных таблиц для каждого сезона
    """

    producer = get_producer()
    conn = db_pool.getconn()

    try:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT DISTINCT league_id, season_id, tournament_id, tournament_stage_id
                FROM seasons
            """)

            for league_id, season_id, tournament_id, tournament_stage_id in cur.fetchall():

                feed = f'to_{tournament_id}_{tournament_stage_id}_1'
                standings = get_data(feed)

                if not standings:
                    continue

                payload = {
                        'league_id': league_id,
                        'season_id': season_id,
                        'tournament_id': tournament_id,
                        'tournament_stage_id': tournament_stage_id,
                        'standings': standings
                    }

                producer.produce(
                    topic='standings',
                    value=json.dumps(payload).encode('utf-8')
                )


    finally:
        producer.produce(
            topic='standings',
            value=json.dumps('message_finally').encode('utf-8')
        )
        producer.flush()
        db_pool.putconn(conn)









def main() :
    c = 0
if __name__ == '__main__':
    main()