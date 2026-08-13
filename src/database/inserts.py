from src.connections import get_connection

from psycopg2.extras import execute_values

REGIONS_INSERT_QUERY = """
    INSERT INTO regions (flashscore_region_id, region_name)
    VALUES %s
    ON CONFLICT (flashscore_region_id)
    DO NOTHING
    """

LEAGUES_INSERT_QUERY = """
    INSERT INTO leagues (
        flashscore_league_feed, 
        competition_type, stage_type, category_id, 
        league_url, league_name, region_id
        )
    VALUES %s
    ON CONFLICT (flashscore_league_feed)
    DO NOTHING
    """

SEASONS_INSERT_QUERY = """
    INSERT INTO seasons (tournament_id, tournament_stage_id, start_date, end_date, is_current, league_id)
    VALUES %s
    ON CONFLICT (tournament_id, tournament_stage_id)
    DO UPDATE SET
    is_current = EXCLUDED.is_current,
    start_date = EXCLUDED.start_date,
    end_date = EXCLUDED.end_date
    """

TEAMS_INSERT_QUERY = """
    INSERT INTO teams (team_name, flashscore_team_feed, flashscore_team_url)
    VALUES %s
    ON CONFLICT (flashscore_team_feed)
    DO NOTHING
    """

RELATIONS_INSERT_QUERY = """
    INSERT INTO season_team_relations (season_id, team_id, count_matches)
    VALUES %s
    ON CONFLICT (season_id, team_id)
    DO UPDATE SET
    count_matches = EXCLUDED.count_matches
    """

MATCHES_INSERT_QUERY = """
    INSERT INTO matches (
        time, flashscore_match_feed, 
        home_team_id, away_team_id, 
        home_score, away_score, 
        home_penalties, away_penalties,
        status, season_id, league_id)
    VALUES %s
    ON CONFLICT (flashscore_match_feed)
    DO NOTHING
    """


def execute_insert(query, data):

    with get_connection() as conn:
        with conn.cursor() as cur:
            execute_values(cur, query, list(data))



def insert_regions(data):
    execute_insert(REGIONS_INSERT_QUERY, data)

def insert_leagues(data):
    execute_insert(LEAGUES_INSERT_QUERY, data)

def insert_seasons(data):
    execute_insert(SEASONS_INSERT_QUERY, data)

def insert_teams(data):
    execute_insert(TEAMS_INSERT_QUERY, data)

def insert_relations(data):
    execute_insert(RELATIONS_INSERT_QUERY, data)

def insert_matches(data):
    execute_insert(MATCHES_INSERT_QUERY, data)