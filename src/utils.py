from src.connections import get_connection




def get_leagues():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT league_id, flashscore_league_feed
                FROM leagues
                """)
            return {el[1]: el[0] for el in cur.fetchall()}

        

def get_regions():
        with get_connection() as conn:
            with conn.cursor() as cur:
                
                cur.execute("""
                SELECT region_id, flashscore_region_id
                FROM regions
                """)
                return {flashscore_region_id: region_id 
                            for region_id, flashscore_region_id 
                            in cur.fetchall()}


def get_league_ids():
    with get_connection() as conn:
         with conn.cursor() as cur:
            cur.execute("""
                SELECT tournament_id, tournament_stage_id, league_id
                FROM seasons
                WHERE is_current = True AND start_date = 0
            """)
            return {(tounament_id, tounament_stage_id): league_id
                    for tounament_id, tounament_stage_id, league_id in cur.fetchall()}