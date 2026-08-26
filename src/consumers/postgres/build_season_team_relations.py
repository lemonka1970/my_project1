from src.kafka_fn import get_consumer
from src.database.queries import get_old_seasons_in_relations, get_team_id_by_feed
from src.database.queries import get_season_id_by_tournamnts, get_league_id_by_tournaments
from src.database.inserts import insert_relations


import json
import logging
logger = logging.getLogger(__name__)




def prepare_relations(payload, old_season_tournaments, teams):

    season_id = payload.get('season_id')
    tournaments = (
        payload.get('tournament_id'), 
        payload.get('tournament_stage_id')
        )
    standings = payload.get('standings')

    if tournaments in old_season_tournaments:
        return None

    

    for el in standings: 
        team_feed = el.get('TI')
        team_id = teams.get(team_feed)
        
        if team_id is None:
            logger.warning("prepare_relations: team %s not in teams", team_feed)
            continue

        row = (
            season_id,
            team_id,
            el.get('TP')
            )

    return [row]





def build_season_team_relations():

    consumer = get_consumer('build_relations')
    consumer.subscribe(['standings'])

    try:
        old_season_tournaments = get_old_seasons_in_relations()
        if not old_season_tournaments:
            logger.error("buil_season_team_relations: list old_season_tournaments is empty")
            raise
        current_league_id = None
        teams = None 


        while True:
            msg = consumer.poll(1.0)

            if msg is None:
                continue
            if msg.error():
                logger.error("build_season_team_relatioins: %s", msg.error())
                continue

            payload = json.loads(msg.value().decode('utf-8'))
            if payload == 'message_finally':
                break

            # держим словарь teams актуальным для текущей лиги
            league_id = payload.get('league_id')
            if league_id != current_league_id:
                current_league_id = league_id
                teams = get_team_id_by_feed(current_league_id)

                if not teams:
                    logger.error("buil_seasons_team_relations: dict teams is empty, league_id: %s", league_id)
                    continue

            relations = prepare_relations(payload, old_season_tournaments, teams)

            if relations:
                insert_relations(relations)
            consumer.commit()

    finally:
        consumer.close()
                


if __name__ == '__main__':
    build_season_team_relations()