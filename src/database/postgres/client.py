from psycopg2 import pool

from dotenv import load_dotenv
import os

load_dotenv()




db_pool = pool.ThreadedConnectionPool(
        minconn=1,
        maxconn=5,
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_PORT'),
        dbname=os.getenv('POSTGRES_DB'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD')
    )


