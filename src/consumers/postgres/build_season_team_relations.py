from src.connections import get_consumer
from src.database.queries import get_old_seasons_in_relations, get_season_id_by_tournamnts, get_league_id_by_tournaments
from src.database.inserts import insert_relations
from src.preparing import prepare_relations
from src.utils import handle_retry

import json
import time


def build_season_team_relations():

    consumer = get_consumer('build_relations')
    consumer.subscribe(['standings'])

    try:
        old_season_tournaments = get_old_seasons_in_relations()
        league_ids = get_league_id_by_tournaments(only_with_dates_resolved=False)
        seasons = get_season_id_by_tournamnts()

        while True:
            msg = consumer.poll(1.0)

            if msg is None:
                continue
            if msg.error():
                print(msg.error())
                continue

            massege = json.loads(msg.value().decode('utf-8'))
            payload = massege.get('payload')

            relations, seasons, league_ids = prepare_relations(payload, old_season_tournaments, seasons, league_ids)

            if relations is None:
                handle_retry(massege, 'standings')
                consumer.commit()
                continue

            if relations:
                insert_relations(relations)
            consumer.commit()

    finally:
        consumer.close()
                


if __name__ == '__main__':
    build_season_team_relations()