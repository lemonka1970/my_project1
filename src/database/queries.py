from src.connections import get_connection

import time

        

def get_region_id_by_flashscore_id():
    # словарь flashscore_region_id: region_id 
    with get_connection() as conn:
        with conn.cursor() as cur:
            
            cur.execute("""
            SELECT region_id, flashscore_region_id
            FROM regions
            """)
            return {flashscore_region_id: region_id 
                        for region_id, flashscore_region_id 
                        in cur.fetchall()}


def get_league_id_by_name(league_id):
    # словарь league_name: league_id, для нужного региона
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                WITH current_region AS (
                    SELECT region_id
                    FROM leagues
                    WHERE league_id = %s
                    )
                SELECT league_id, league_name
                FROM leagues
                JOIN current_region USING(region_id)
                """, (league_id, ))
            return {league_name: league_id for league_id, league_name in cur.fetchall()}






def get_league_id_by_flashscore_feed():
    # словарь flashscore_league_feed: league_id

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT league_id, flashscore_league_feed
                FROM leagues
                """)
            return {flashscore_league_feed: league_id for league_id, flashscore_league_feed in cur.fetchall()}




def get_league_id_by_tournaments():
    # словарь (tounament_id, tounament_stage_id): league_id

    with get_connection() as conn:
         with conn.cursor() as cur:
            cur.execute("""
                SELECT tournament_id, tournament_stage_id, league_id
                FROM seasons
                WHERE is_current = True AND start_date = 0
            """)
            return {(tounament_id, tounament_stage_id): league_id
                    for tounament_id, tounament_stage_id, league_id in cur.fetchall()}


def get_season_id_by_tournamnts():
    # словарь (tounament_id, tounament_stage_id): season_id

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT tournament_id, tournament_stage_id, season_id
                FROM seasons
                """)
            return {(tournament_id, tournament_stage_id): season_id 
                    for tournament_id, tournament_stage_id, season_id 
                    in cur.fetchall()}




def get_team_id_by_feed(league_id):
    # словарь {команда: id команды} для конкретной лиги

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT team_id, flashscore_team_feed
                FROM teams
                JOIN season_team_relations USING(team_id)
                JOIN seasons USING(season_id)
                WHERE league_id = %s
                """, (league_id,))
            return {flashscore_team_feed: team_id 
                    for team_id, flashscore_team_feed 
                    in cur.fetchall()}




def get_old_seasons_in_relations():
    # сет уже ранее обработанных сезонов в таблице sesason_team_relations

    with get_connection() as conn:
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



def resolve_with_retry(cache: dict, key, refresh_func, sleep_time=10, max_attemps=None):
    attemps = 0

    while True:
        result = cache.get(key)
        if result is not None:
            return result, cache

        if max_attemps and attemps > max_attemps:
            raise

        time.sleep(sleep_time)
        cache = refresh_func()
        attemps += 1

