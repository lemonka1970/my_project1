from src.database.postgres.client import db_pool
from src.database.clickhouse.client import get_ch_client

from psycopg2 import sql
from datetime import datetime

import logging
logger = logging.getLogger(__name__)


def get_max_id_from_postgres(db_table, id_column):
    # по таблице и колонке идентификатора 
    # возвращаем максимальное значение идентификатора

    conn = db_pool.getconn()

    query = sql.SQL("""
    SELECT MAX({id_column})
    FROM {db_table}
    """).format(
        id_column = sql.Identifier(id_column),
        db_table = sql.Identifier(db_table)
    )


    try:
        with conn.cursor() as cur:

            cur.execute(query)
            max_id = cur.fetchone()[0]

        return max_id

    finally:
        db_pool.putconn(conn)
        




def get_max_id_from_clickhouse(db_table, id_column):
    # по таблице и колонке идентификатора 
    # возвращаем максимальное значение идентификатора

    client = get_ch_client()

    db_table = 'row.' + db_table
    query = f"""
    SELECT MAX({id_column})
    FROM {db_table}
    """

    max_id = client.query(query)
    return max_id.result_rows[0][0] or 0





def get_id_current_seasons():
    # возвращает список id-шников всех последних и предпоследних сезонов
    conn = db_pool.getconn()

    ids = []

    query = """
    WITH ranked AS (
        SELECT 
            season_id, 
            ROW_NUMBER() over(PARTITION BY league_id ORDER BY start_date DESC) as rank
        FROM seasons
        )
    SELECT season_id
    FROM ranked
    WHERE rank in (1, 2)
    """

    try:
        with conn.cursor() as cur:
            cur.execute(query)
            ids = [el[0] for el in cur.fetchall()]

        return ids

    finally:
        db_pool.putconn(conn)

        





def get_data_with_ids(db_table=['seasons', 'season_team_relations'], columns=None, id_column=None, ids_current_seaons=None):
    # собираем данные для таблиц seasons и season_team_relations по текущим и предыдущим сезонам
    conn = db_pool.getconn()

    data = None
    
    query = sql.SQL("""
    SELECT {columns}
    FROM {db_table}
    WHERE {id_column} IN %s
    """).format(
        columns = sql.SQL(', ').join(
            sql.Identifier(col) for col in columns
        ),
        db_table = sql.Identifier(db_table),
        id_column = sql.Identifier(id_column)
    )

    try:
        with conn.cursor() as cur:
            cur.execute(query, (ids_current_seaons, ))
            data = cur.fetchall()

        return data

    finally:
        db_pool.putconn(conn)

        



def get_data_from_postgres(db_table, columns, id_column, min_id, max_id):
    # возвращает данные по колонке и максимальному и минимальному айдишнику

    conn = db_pool.getconn()

    data = None
    query = sql.SQL("""
        SELECT {columns}
        FROM {table}
        WHERE {id_column} >= %s
        AND {id_column} < %s
        ORDER BY {id_column}
        """).format(
            columns = sql.SQL(", ").join(
                sql.Identifier(col) for col in columns
            ),
            table = sql.Identifier(db_table),
            id_column = sql.Identifier(id_column)
        )


    try:
        with conn.cursor() as cur:

            cur.execute(query, (min_id, max_id))
            data = cur.fetchall()

        return data

    finally:
        db_pool.putconn(conn)
        



def sync_table_to_clichouse(db_table: str, columns: list, id_column: str, mode=['initialize_append', 'update']):
    client =  get_ch_client()

    ch_columns = columns.copy()
    if db_table in ['seasons', 'season_team_relations']:
        ch_columns.append('updated_at')


    if mode == 'initialize_append':
        max_id_postgres = get_max_id_from_postgres(db_table, id_column)
        max_id_clickhouse = get_max_id_from_clickhouse(db_table, id_column)


        for lower_bounds in range(max_id_clickhouse, max_id_postgres + 10001, 10000):
            upper_bounds = lower_bounds + 10000

            data = get_data_from_postgres(db_table, columns, id_column, lower_bounds, upper_bounds)

            # для ReplacingMergeTree таблиц
            if db_table in ['seasons', 'season_team_relations']:
                data = [
                    row + (datetime.now(),)
                    for row in data
                ]
            
            client.insert('row.' + db_table, data, ch_columns)


    elif mode == 'update':
        data = get_data_with_ids(db_table, columns, id_column, get_id_current_seasons())
        data = [
            row + (datetime.now(),)
            for row in data
        ]
        client.insert('row.' + db_table, data, ch_columns)


    

        

def sync_regioins():
    sync_table_to_clichouse('regions', 
                            ['region_id', 'region_name'],
                            'region_id',
                            'initialize_append')

def sync_leagues():
    sync_table_to_clichouse('leagues',
                            ['league_id', 'competition_type', 'stage_type', 'category_id', 'league_name', 'region_id'],
                            'league_id',
                            'initialize_update')

def sync_seasons():
    sync_table_to_clichouse('seasons',
                            ['season_id', 'start_date', 'end_date', 'is_current', 'league_id'],
                            'season_id',
                            'update')
    sync_table_to_clichouse('seasons', 
                            ['season_id', 'start_date', 'end_date', 'is_current', 'league_id'],
                            'season_id',
                            'initialize_update')

def sync_teams():
    sync_table_to_clichouse('teams',
                            ['team_id', 'team_name'],
                            'team_id',
                            'initialize_append')

def sync_relations():
    sync_table_to_clichouse('season_team_relations',
                            ['season_id', 'team_id', 'count_matches'],
                            'season_id',
                            'update')
    sync_table_to_clichouse('season_team_relations',
                            ['season_id', 'team_id', 'count_matches'],
                            'season_id',
                            'initialize_append')

def sync_matches():
    sync_table_to_clichouse('matches',
                            ['match_id', 'time', 'home_team_id', 'away_team_id', 'home_score', 'away_score',
                             'home_penalties', 'away_penalties', 'status', 'season_id', 'league_id'],
                             'match_id',
                             'initialize_append')