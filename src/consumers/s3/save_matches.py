from src.connections import get_consumer, get_client

import json
import io




def save_matches():

    consumer = get_consumer('save_matches')
    consumer.subscribe(['update_matches'])

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

            url_team_1 = payload.get('url_team_1')
            url_team_2 = payload.get('url_team_2')
            h2h = payload.get('h2h')

            object_name = f'matches/{url_team_1}/{url_team_2}'
            h2h = json.dumps(h2h).encode('utf-8')

            client.put_object(
                bucket_name = 'football-row',
                object_name = object_name,
                data = io.BytesIO(h2h),
                length = len(h2h)
            )

    finally:
        consumer.close()




if __name__ == '__main__':
    save_matches()