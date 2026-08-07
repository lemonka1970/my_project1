from src.connections import get_consumer, get_client

import json
import io




def save_scoreboards():

    consumer = get_consumer('save_scoreboards')
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
            date = payload.get('date')
            scoreboard = payload.get('scoreboards')

            if scoreboard[0].get('~ZA'):
                full_name_league = scoreboard[0].get('~ZA')
                object_name = f'scoreboargs/{date}/{full_name_league}'

                scoreboard = json.dumps(scoreboard).encode('utf-8')

                client.put_object(
                    bucket_name = 'football-row',
                    object_name = object_name,
                    data = io.BinaryIO(scoreboard),
                    len = len(scoreboard)
                )

    finally:
        consumer.close()




if __name__ == '__main__':
    save_scoreboards()