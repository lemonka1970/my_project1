from airflow import DAG
from airflow.operators.python import PythonOperator

from datetime import datetime, timedelta
from src.kafka_fn import create_topics
from src.producers_matches import produce_initializetion_matches
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

    initialize_matches = PythonOperator(
        task_id='produce_initialize_matches',
        python_callable=produce_initializetion_matches
    )

    topics >> initialize_matches
