from src.connections import get_consumer, get_client

import json
import io




def save_past_seasons():

    consumer = get_consumer('save_past_seasons')
    consumer.subscribe(['past_seasons'])

    client = get_client()

    try:
        while True:
            msg = consumer.poll(1.0)

            if msg is None:
                continue
            if msg.error():
                print(msg.error())
                continue

            message = json.loads(msg.value().decode('utf-8'))
            payload = message.get('payload')

            tournament_id = payload.get('tournament_id')
            tournament_stage_id = payload.get('tournament_stage_id')
            past_seasons = payload.get('past_seasons')

            object_name = f'past_seasons/{tournament_id}/{tournament_stage_id}'
            past_seasons = json.dumps(past_seasons).encode('utf-8')

            client.put_object(
                bucket_name = 'football-row',
                object_name = object_name,
                data = io.BytesIO(past_seasons),
                length = len(past_seasons)
            )

    finally:
        consumer.close()




if __name__ == '__main__':
    save_past_seasons()