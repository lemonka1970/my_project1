from src.connections import get_consumer
from src.database.queries import get_old_seasons_in_relations, get_season_id_by_tournamnts
from src.database.inserts import insert_relations
from src.preparing import prepare_relations

import json
import time


def build_season_team_relations():

    consumer = get_consumer('build_relations')
    consumer.subscribe(['standings'])

    try:
        old_season_tournaments = get_old_seasons_in_relations()
        seasons = get_season_id_by_tournamnts()

        while True:
            msg = consumer.poll(1.0)

            if msg is None:
                continue
            if msg.error():
                print(msg.error())
                continue

            payload = json.loads(msg.value().decode('utf-8'))

            relations, seasons = prepare_relations(payload, old_season_tournaments, seasons)


            insert_relations(relations)

    finally:
        consumer.close()
                


if __name__ == '__main__':
    build_season_team_relations()