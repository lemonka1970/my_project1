from src.connections import get_consumer, get_client

import json
import io




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
                print(msg.error())
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

    finally:
        consumer.close()




if __name__ == '__main__':
    save_standings()