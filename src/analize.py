from src.parsing import get_connection
import pandas as pd

def get_standings(season_id):
    """
    По season_id формирует и возвращает турнирную таблицу
    """

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute("""
                WITH matches_info AS (
                    SELECT t.team_name, 1 AS matches_played, 
                        m.home_score AS goals_for, m.away_score AS goals_against,
                        CASE 
                            WHEN m.home_score > m.away_score THEN 1
                            ELSE 0 
                        END AS wins,
                        CASE 
                            WHEN m.home_score = m.away_score THEN 1
                            ELSE 0
                        END AS draws,
                        CASE
                            WHEN m.home_score < m.away_score THEN 1
                            ELSE 0
                        END AS loss,
                        CASE
                            WHEN m.home_score > m.away_score THEN 3
                            WHEN m.home_score = m.away_score THEN 1
                            ELSE 0
                        END AS points
                    FROM matches m
                    JOIN teams t ON m.home_team_id = t.team_id
                    WHERE m.season_id = %s

                    UNION ALL

                    SELECT t.team_name, 1 AS matches_played, 
                        m.away_score AS goals_for, m.home_score AS goals_against, 
                        CASE
                            WHEN m.home_score < m.away_score THEN 1
                            ELSE 0 
                        END AS wins,
                        CASE 
                            WHEN m.home_score = m.away_score THEN 1
                            ELSE 0
                        END AS draws,
                        CASE
                            WHEN m.home_score > m.away_score THEN 1
                            ELSE 0
                        END AS loss,
                        CASE
                            WHEN m.home_score < m.away_score THEN 3
                            WHEN m.home_score = m.away_score THEN 1
                            ELSE 0
                        END AS points
                    FROM matches m
                    JOIN teams t ON m.away_team_id = t.team_id
                    WHERE m.season_id = %s
                        )

                    table AS (
                        SELECT team_name, 
                        SUM(matches_played) AS matches_played, 
                        SUM(wins) AS wins, 
                        SUM(draws) AS draws, 
                        SUM(loss) AS loss,
                        SUM(goals_for) AS goals_for,
                        SUM(goals_against) AS goals_against,
                        SUM(goals_for) - SUM(goals_defference) AS goals_difference,
                        SUM(points) AS points
                    FROM matches_info
                    GROUP BY team_name
                        )

                    SELECT ROW_NUMBER() OVER(ORDER BY points DESC) AS rank,
                        team_name, matches_played, wins, draws, loss, goals_for, goals_against, goals_difference, points
                    FROM table
                    ORDER BY points DESC

            """, (season_id, season_id, ))

            return pd.DataFrame(cur.fetchall(), columns=[desc[0] for desc in cur.description()])



def main():

    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
        SELECT *
        FROM seasons
        """)

        for el in cur.fetchall():
            print(el)


if __name__ == "__main__":
    main()