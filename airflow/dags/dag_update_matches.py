from airflow import DAG
from airflow.operators.python import PythonOperator

from datetime import datetime, timedelta
from src.parsing import (fetch_seasons, update_matches)


default_args = {
    'start_date': datetime(2026, 1, 1),
    'retries': 5,
    'retry_delay': timedelta(minutes=1)
}


with DAG(
    dag_id = 'update_matches',
    schedule_interval = '@daily',
    catchup = False,
    default_args = default_args
)as dag:

    seasons = PythonOperator(
        task_id = 'fetch_seasons',
        python_callable = fetch_seasons
    )

    matches = PythonOperator(
        task_id = 'update_matches',
        python_callable = update_matches
    )

    seasons >> matches