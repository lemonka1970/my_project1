from src.database.postgres_conn import db_pool


        

def get_region_id_by_flashscore_id():
    # словарь flashscore_region_id: region_id 
    conn = db_pool.getconn()

    try:
        with conn.cursor() as cur:
            cur.execute("""
            SELECT region_id, flashscore_region_id
            FROM regions
            """)
            return {flashscore_region_id: region_id 
                        for region_id, flashscore_region_id 
                        in cur.fetchall()}
    finally:
        db_pool.putconn(conn)



def get_league_id_by_name():
    # словарь full_league_name: league_id, для нужного региона
    conn = db_pool.getconn()

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT CONCAT(region_name, ': ', league_name), league_id
                FROM leagues
                JOIN regions USING(region_id)
                """)
            return {full_league_name: league_id for full_league_name, league_id in cur.fetchall()}
    finally:
        db_pool.putconn(conn)






def get_league_id_by_flashscore_feed():
    # словарь flashscore_league_feed: league_id
    conn = db_pool.getconn()

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT league_id, flashscore_league_feed
                FROM leagues
                """)
            return {flashscore_league_feed: league_id for league_id, flashscore_league_feed in cur.fetchall()}
    finally:
        db_pool.putconn(conn)




def get_league_id_by_tournaments():
    # словарь (tounament_id, tounament_stage_id): league_id

    conn = db_pool.getconn()

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT tournament_id, tournament_stage_id, league_id
                FROM seasons
                WHERE is_current = True
            """)
            return {(tounament_id, tounament_stage_id): league_id
                    for tounament_id, tounament_stage_id, league_id in cur.fetchall()}
    finally:
        db_pool.putconn(conn)


    



def get_season_id_by_tournamnts():
    # словарь (tounament_id, tounament_stage_id): season_id
    conn = db_pool.getconn()

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT tournament_id, tournament_stage_id, season_id
                FROM seasons
                """)
            return {(tournament_id, tournament_stage_id): season_id 
                    for tournament_id, tournament_stage_id, season_id 
                    in cur.fetchall()}
    finally:
        db_pool.putconn(conn)




def get_team_id_by_feed():
    # словарь {команда: id команды}
    conn = db_pool.getconn()

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT team_id, flashscore_team_feed
                FROM teams
                """)
            return {flashscore_team_feed: team_id 
                    for team_id, flashscore_team_feed 
                    in cur.fetchall()}
    finally:
        db_pool.putconn(conn)



def get_old_seasons_in_relations():
    # сет уже ранее обработанных сезонов в таблице sesason_team_relations

    conn = db_pool.getconn()

    try:
        with conn.cursor() as cur:
            cur.execute("""
                WITH unique_seasons AS (
                SELECT DISTINCT season_id
                FROM season_team_relations
            ),
            seasons_q AS (
                SELECT
                    s.tournament_id,
                    s.tournament_stage_id,
                    ROW_NUMBER() OVER (
                        PARTITION BY s.league_id
                        ORDER BY s.start_date DESC
                    ) AS num
                FROM unique_seasons us
                JOIN seasons s USING (season_id)
            )
            SELECT tournament_id, tournament_stage_id
            FROM seasons_q
            WHERE num > 2;
                """)
            return set((tournament_id, tournament_stage_id)
                        for tournament_id, tournament_stage_id 
                        in cur.fetchall())
    finally:
        db_pool.putconn(conn)


