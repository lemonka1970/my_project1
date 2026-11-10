from airflow import DAG
from airflow.operators.python import PythonOperator

from datetime import datetime, timedelta
from src.kafka_fn import create_topics
from src.producers.metadata import produce_scoreboards, produce_past_seasons, produce_standings
from src.consumers.fetch_regions import fetch_regions
from src.consumers.fetch_leagues import fetch_leagues
from src.consumers.fetch_current_seasons import fetch_current_seasons
from src.consumers.fetch_seasons import fetch_seasons
from src.consumers.fetch_teams import fetch_teams
from src.consumers.build_season_team_relations import build_season_team_relations

default_args = {
    'start_date': datetime(2026, 1, 1),
    'retries': 3,
    'retry_delay': timedelta(seconds=5)
}

with DAG(
    dag_id = 'refresh_matadata',
    schedule_interval = None,
    catchup = False,
    default_args = default_args
) as dag:

    topiks = PythonOperator(
        task_id = 'create_topics',
        python_callable = create_topics
    )

    scoreboards = PythonOperator(
        task_id = 'produce_scoreboards',
        python_callable = produce_scoreboards
    )

    regions = PythonOperator(
        task_id = 'fetch_regions',
        python_callable = fetch_regions
    )

    leagues = PythonOperator(
        task_id = 'fetch_leagues',
        python_callable = fetch_leagues
    )

    current_seasons = PythonOperator(
        task_id = 'fetch_current_seasons',
        python_callable = fetch_current_seasons
    )

    past_seasons = PythonOperator(
        task_id = 'produce_past_seasons',
        python_callable = produce_past_seasons
    )

    seasons = PythonOperator(
        task_id = 'fetch_seasons',
        python_callable = fetch_seasons
    )

    standings = PythonOperator(
        task_id = 'produce_standings',
        python_callable = produce_standings
    )

    teams = PythonOperator(
        task_id = 'fetch_teams',
        python_callable = fetch_teams
    )

    relations = PythonOperator(
        task_id = 'build_season_team_relations',
        python_callable = build_season_team_relations
    )

    topiks >> scoreboards
    scoreboards >> regions >> leagues >> current_seasons >> past_seasons
    past_seasons >> seasons >> standings
    standings >> teams >> relations
