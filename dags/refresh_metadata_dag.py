from airflow import DAG
from airflow.operators.python import PythonOperator

from datetime import datetime, timedelta
from src.parsing_func import (fetch_regions, fetch_leagues, fetch_seasons,
                                   fetch_teams, build_season_team_relations, update_matches)

default_args = {
    'start_date': datetime(2026, 1, 1),
    'retries': 5,
    'retry_delay': timedelta(minutes=30)
}

with DAG(
    dag_id = 'update_leagues',
    schedule = '@weekly',
    catchup = False,
    default_args=default_args
):

    regions = PythonOperator(
        task_id = 'fetch_regions',
        python_callable = fetch_regions
    )

    leagues = PythonOperator(
        task_id = 'fetch_leagues',
        python_callable = fetch_leagues
    )

    seasons = PythonOperator(
        task_id = 'fetch_seasons',
        python_callable = fetch_seasons
    )

    teams = PythonOperator(
        task_id = 'fetch_teams',
        python_callable = fetch_teams
    )

    relations = PythonOperator(
        task_id = 'build_relations',
        python_callable = build_season_team_relations
    )

    regions >> leagues >> seasons >> teams >> relations



with DAG(
    dat_id = 'update_matches',
    schedule = '@daily',
    catchup = False,
    dafault_args = default_args
):

    seasons = PythonOperator(
        task_id = 'fetch_seasons',
        python_callable = fetch_seasons
    )

    matches = PythonOperator(
        task_id = 'update_matches',
        python_callable = update_matches
    )

    seasons >> matches