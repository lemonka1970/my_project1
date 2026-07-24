import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()



def get_connection():
    return psycopg2.connect(host=os.getenv('HOST'),
                            port=5432,
                            dbname=os.getenv('DB_NAME'),
                            user='postgres',
                            password='postgres')





def initialize_database():
    """
    Инициализирует базу данных и таблицы
    """

    # conn = get_connection()
    # conn.autocommit = True
    # cur = conn.cursor()
    #
    # cur.execute("""
    # SELECT 1 FROM pg_database WHERE datname = %s
    # """, ('football_core', ))
    #
    # if cur.fetchone() is None:
    #     cur.execute("""
    #     CREATE DATABASE football_core
    #     """)
    #
    # cur.close()
    # conn.close()


    conn = get_connection()
    try:
        with conn.cursor() as cur:
            

            cur.execute("""
            CREATE TABLE IF NOT EXISTS regions (
            region_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            flashscore_region_id INT UNIQUE NOT NULL,
            region_name TEXT UNIQUE NOT NULL
            )
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS leagues (
            league_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            flashscore_league_feed VARCHAR(8) UNIQUE NOT NULL,
            competition_type VARCHAR(1) NOT NULL,
            stage_type INT,
            category_id INT NOT NULL,
            league_url TEXT UNIQUE NOT NULL,
            league_name TEXT NOT NULL,
            region_id INT REFERENCES regions(region_id)
            )
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS seasons (
            season_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            tournament_id VARCHAR(8) NOT NULL,
            tournament_stage_id VARCHAR(8) NOT NULL,
            start_date INT,
            end_date INT,
            is_current BOOLEAN NOT NULL,
            league_id INT REFERENCES leagues(league_id),
            UNIQUE(tournament_id, tournament_stage_id)
            )
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS teams 
            (
                team_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                team_name TEXT NOT NULL,
                flashscore_team_feed VARCHAR(8) UNIQUE NOT NULL,
                flashscore_team_url TEXT UNIQUE NOT NULL
            )
            """)


            cur.execute("""
            CREATE TABLE IF NOT EXISTS season_team_relations
            (
                season_id INT NOT NULL REFERENCES seasons (season_id),
                team_id   INT NOT NULL REFERENCES teams (team_id),
                count_matches INT NOT NULL,
                UNIQUE (season_id, team_id)
            )
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS matches (
            match_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            time TIMESTAMP NOT NULL,
            flashscore_match_feed VARCHAR(8) UNIQUE NOT NULL,
            home_team_id INT NOT NULL REFERENCES teams(team_id),
            away_team_id INT NOT NULL REFERENCES teams(team_id),
            home_score INT,
            away_score INT,
            home_penalties INT,
            away_penalties INT,
            status VARCHAR(10),
            season_id INT REFERENCES seasons(season_id),
            league_id INT REFERENCES leagues(league_id)
            )
            """)

            cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_matches_time
            ON matches(time);
            
            CREATE INDEX IF NOT EXISTS idx_matches_home
            ON matches(home_team_id);
                
            CREATE INDEX IF NOT EXISTS idx_matches_away
            ON matches(away_team_id)
            """)


            conn.commit()
            
        conn.close()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def main():

    c = 0

if __name__ == '__main__':
    main()
