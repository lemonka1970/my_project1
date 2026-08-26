from src.kafka_fn import get_consumer
from src.database.minio_client import get_client

import json
import io

import logging
logger = logging.getLogger(__name__)




def save_standings():

    consumer = get_consumer('save_standings')
    consumer.subscribe(['standings'])

    client = get_client()

    try:
        while True:
            msg = consumer.poll(1.0)

            if msg is None:
                continue
            if msg.error():
                logger.error("save_standings: %s", msg.error())
                continue

            message = json.loads(msg.value().decode('utf-8'))
            payload = message.get('payload')
            
            tournament_id = payload.get('tournament_id')
            tournament_stage_id = payload.get('tournament_stage_id')
            standings = payload.get('standings')

            object_name = f'standings/{tournament_id}/{tournament_stage_id}'

            standings = json.dumps(standings).encode('utf-8')

            client.put_object(
                bucket_name = 'football-row',
                object_name = object_name,
                data = io.BytesIO(standings),
                length = len(standings)
            )

            consumer.commit()

    finally:
        consumer.close()




if __name__ == '__main__':
    save_standings()