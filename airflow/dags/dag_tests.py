from airflow import DAG
from airflow.operators.python import PythonOperator

from datetime import datetime, timedelta

from src.kafka_fn import create_topics
from src.producers_metadata import produce_standings
from src.consumers.postgres.build_season_team_relations import build_season_team_relations


default_args = {
    'start_date': datetime(2026, 1, 1),
    'retries': 3,
    'retry_delay': timedelta(seconds=5)
}

with DAG(
    dag_id = 'tests',
    schedule_interval = None,
    catchup = False,
    default_args = default_args
) as dag:

    topics = PythonOperator(
        task_id = 'create_topics',
        python_callable = create_topics
    )
    
    standings = PythonOperator(
        task_id = 'produce_standings',
        python_callable = produce_standings
    )

    relations = PythonOperator(
        task_id = 'relations',
        python_callable = build_season_team_relations
    )



    topics >> standings >> relations