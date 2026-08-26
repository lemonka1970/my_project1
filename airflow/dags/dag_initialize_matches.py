from airflow import DAG
from airflow.operators.python import PythonOperator

from datetime import datetime, timedelta
from src.kafka_fn import create_topics
from src.producers_matches import produce_initializetion_matches
from src.producers_metadata import produce_scoreboards, produce_past_seasons
from src.consumers.postgres.fetch_current_seasons import fetch_current_seasons
from src.consumers.postgres.fetch_seasons import fetch_seasons
from src.consumers.postgres.fetch_initializetion_matches import fetch_initializetion_matches

default_args = {
    'start_date': datetime(2020, 1, 1),
    'retries': 3,
    'retry_delay': timedelta(minutes=1)
}

with DAG(
    dag_id='initialize_matches',
    schedule_interval=None,
    catchup=False,
    default_args=default_args
) as dag:

    topics = PythonOperator(
        task_id = 'create_topics',
        python_callable = create_topics
    )
    
    scoreboards = PythonOperator(
        task_id = 'produce_scoreboards',
        python_callable = produce_scoreboards
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

    initialize_matches = PythonOperator(
        task_id='produce_initialize_matches',
        python_callable=produce_initializetion_matches
    )

    fetch_initialize_matches = PythonOperator(
        task_id = 'fetch_initializetion_matches',
        python_callable = fetch_initializetion_matches
    )

    topics >> scoreboards
    scoreboards >> current_seasons >> past_seasons
    past_seasons >> seasons >> initialize_matches
    initialize_matches >> fetch_initialize_matches
