from airflow import DAG
from airflow.operators.python import PythonOperator

from datetime import datetime, timedelta
from src.producers import produce_scoreboards, produce_past_seasons

default_args = {
    'start_date': datetime(2026, 1, 1),
    'retries': 3,
    'retry_delay': timedelta(minutes=2)
}

with DAG(
    dag_id = 'refresh_matadata',
    schedule_interval = '@weekly',
    catchup = False,
    default_args = default_args
) as dag:

    scoreboards = PythonOperator(
        task_id = 'produce_scoreboards',
        python_callable = produce_scoreboards
    )

    past_seasons = PythonOperator(
        task_id = 'produce_past_seasons',
        python_callable = produce_past_seasons
    )

    [scoreboards, past_seasons]