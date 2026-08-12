from airflow import DAG
from airflow.operators.python import PythonOperator

from datetime import datetime, timedelta
from src.producers import produce_scoreboards, produce_past_seasons
from src.producers import produce_updeting_matches


default_args = {
    'start_date': datetime(2026, 1, 1),
    'retries': 5,
    'retry_delay': timedelta(minutes=1)
}


with DAG(
    dag_id = 'update_matches',
    schedule_interval = None,
    catchup = False,
    default_args = default_args
)as dag:

    scoreboard = PythonOperator(
        task_id = 'produce_scoreboard',
        python_callable = produce_scoreboards
    )

    past_seasons = PythonOperator(
        task_id = 'past_seasons',
        python_callable = produce_past_seasons
    )

    matches = PythonOperator(
        task_id = 'update_matches',
        python_callable = produce_updeting_matches
    )

    scoreboard >> past_seasons >> matches
