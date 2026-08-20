from src.connections import get_consumer, get_connection
from src.database.queries import get_old_seasons_in_relations, get_team_id_by_feed
from src.database.queries import get_season_id_by_tournamnts, get_league_id_by_tournaments
from src.database.inserts import insert_relations


import json
import logging
logger = logging.getLogger(__name__)




def prepare_relations(payload, old_season_tournaments, seasons, leagues, cur):

    tournaments = (payload.get('tournament_id'), payload.get('tournament_stage_id'))
    standings = payload.get('standings')

    if tournaments in old_season_tournaments:
        return None
    
    season_id = seasons.get(tournaments)
    league_id = leagues.get(tournaments)
    

    relations = set()


    for el in standings: 
        teams = get_team_id_by_feed(league_id, cur)
        team_feed = el.get('TI')
        team_id = teams.get(team_feed)

        relations.add((
            season_id,
            team_id,
            el.get('TP')
            ))

    return relations





def build_season_team_relations():

    consumer = get_consumer('build_relations')
    consumer.subscribe(['standings'])

    try:
        old_season_tournaments = get_old_seasons_in_relations()
        leagues = get_league_id_by_tournaments(only_with_dates_resolved=False)
        seasons = get_season_id_by_tournamnts()

        with get_connection() as conn:
            with conn.cursor() as cur:

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

                    relations = prepare_relations(payload, old_season_tournaments, seasons, leagues, cur)

                    if relations:
                        insert_relations(relations)
                    consumer.commit()

    finally:
        consumer.close()
                


if __name__ == '__main__':
    build_season_team_relations()