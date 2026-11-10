import clickhouse_connect 

from dotenv import load_dotenv
import os
load_dotenv()

def get_ch_client():
    return clickhouse_connect.get_client(
        host='clickhouse', port=8123,
        username=os.getenv('CLICKHOUSE_USER'), password=os.getenv('CLICKHOUSE_PASSWORD'),
        database=os.getenv('CLICKHOUSE_DB')
    )