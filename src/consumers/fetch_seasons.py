from src.connections import get_connection, get_consumer
from src.utils import get_league_ids

import time
import json
from psycopg2.extras import execute_values






def fetch_seasons():
    """
    правим даты в уже загруженных текущих сезонах и добавляем новые исторические из топика past_seasons
    """


    consumer = get_consumer('fetch_seasons')
    consumer.subscribe(['past_seasons'])

    query = """
        INSERT INTO seasons (tournament_id, tournament_stage_id, start_date, end_date, is_current, league_id)
        VALUES %s
        ON CONFLICT (tournament_id, tournament_stage_id)
        DO UPDATE SET
        is_current = EXCLUDED.is_current,
        start_date = EXCLUDED.start_date,
        end_date = EXCLUDED.end_date
        """

    try:
        # league_ids возвращает id лиги по (tournament_id, tournament_stage_id) текущего сезона
        league_ids = get_league_ids() 



        while True:
            # получаем message
            msg = consumer.poll(1.0)

            if msg is None:
                continue
            if msg.error():
                print(msg.error())
                continue

            payload = json.loads(msg.value().decode('utf-8'))
            data = payload.get('past_seasons')
            if not data:
                continue

            seasons = set()

            # id-шники текушего сезона
            tournament_id = payload.get('tournament_id')
            tournament_stage_id = payload.get('tournament_stage_id')

            # если эту лигу еще не успелли обработать
            while True:
                league_id = league_ids.get((tournament_id, tournament_stage_id))
                if league_id is not None:
                    break

                time.sleep(10)
                league_ids = get_league_ids()



            current_row = [tournament_id,
                            tournament_stage_id,
                            0, 0, True,
                            league_id
                            ]

            # правим даты текущего сезона и загружаем и его тоже
            start = int(data[0]["start"])
            end = int(data[0]["end"])

            current_row[2] = start + 1
            current_row[3] = end + 1
            seasons.add(tuple(current_row))

            # и проходимся по остальным сезонам
            for el in data:
                row = [el.get('tournamentId'),
                    el.get('tournamentStages').get('other')[0].get('id'),
                    el.get('start'),
                    el.get('end'),
                    False,
                    current_row[5],
                    ]

                seasons.add(tuple(row))


            with get_connection() as conn:
                with conn.cursor() as cur:
                    execute_values(cur, query, list(seasons))
            
            consumer.commit()

    finally:
        consumer.close()
        


if __name__ == '__main__':
    fetch_seasons()