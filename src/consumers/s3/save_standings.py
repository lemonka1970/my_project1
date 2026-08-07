from src.connections import get_consumer, get_client

import json
import io




def save_standings():

    consumer = get_consumer('save_standings')
    client = get_client()

    try:
        while True:
            msg = consumer.poll(1.0)

            if msg is None:
                continue
            if msg.error():
                print(msg.error())
                continue

            payload = json.loads(msg.value().decode('utf-8'))
            feed_season = payload.get('feed_season')
            standings = payload.get('standings')

            object_name = f'standings/{feed_season}'

            standings = json.dumps(standings).encode('utf-8')

            client.put_object(
                bucket_name = 'football-row',
                object_name = object_name,
                data = io.BinaryIO(standings),
                len = len(standings)
            )

    finally:
        consumer.close()




if __name__ == '__main__':
    save_standings()