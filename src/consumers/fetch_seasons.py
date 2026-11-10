from src.kafka_fn import get_consumer
from src.database.postgres.queries import get_league_id_by_tournaments
from src.database.postgres.inserts import insert_seasons

import json
import logging
logger = logging.getLogger(__name__)






def prepare_seasons(payload, league_ids):

    past_seasons = payload.get('past_seasons')

    seasons = set()

    # id-шники текушего сезона
    tournament_id = payload.get('tournament_id')
    tournament_stage_id = payload.get('tournament_stage_id')

    league_id = league_ids.get((tournament_id, tournament_stage_id))
    if league_id is None:
        logger.warning("prepare_seasons: league (%s, %s) is not in league_ids", tournament_id, tournament_stage_id)
        return None


    current_row = [tournament_id,
                    tournament_stage_id,
                    0, 0, True,
                    league_id
                    ]

    # правим даты текущего сезона и загружаем и его тоже
    start = int(past_seasons[0]["start"])
    end = int(past_seasons[0]["end"])

    current_row[2] = start + 1
    current_row[3] = end + 1
    seasons.add(tuple(current_row))

    # и проходимся по остальным сезонам
    for el in past_seasons:
        row = [el.get('tournamentId'),
            el.get('tournamentStages').get('other')[0].get('id'),
            el.get('start'),
            el.get('end'),
            False,
            current_row[5],
            ]

        seasons.add(tuple(row))

    return seasons







def fetch_seasons():
    """
    правим даты в уже загруженных текущих сезонах и добавляем новые исторические из топика past_seasons
    """


    consumer = get_consumer('fetch_seasons')
    consumer.subscribe(['past_seasons'])

    try:
        # league_ids возвращает id текущих сезонов по (tournament_id, tournament_stage_id) 
        league_ids = get_league_id_by_tournaments()  
        if not league_ids:
            logger.error("fetch_seasons: dict league_ids is empty") 
            raise

        while True:
            # получаем message
            msg = consumer.poll(1.0)

            if msg is None:
                continue
            if msg.error():
                logger.error('fetch_seasons: %s', msg.error())
                continue

            payload = json.loads(msg.value().decode('utf-8'))
            if payload == 'message_finally':
                break
            
            seasons = prepare_seasons(payload, league_ids)

            if seasons:
                insert_seasons(seasons)
            
            consumer.commit()

    finally:
        consumer.close()
        


if __name__ == '__main__':
    fetch_seasons()