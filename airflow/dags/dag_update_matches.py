from airflow import DAG
from airflow.operators.python import PythonOperator

from datetime import datetime, timedelta
from src.kafka_fn import create_topics
from src.producers_matches import produce_updeting_matches


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

    topics = PythonOperator(
        task_id = 'create_topics',
        python_callable = create_topics
        )


    update_matches = PythonOperator(
        task_id='produce_updating_matches',
        python_callable=produce_updeting_matches
    )


    topics >> update_matches

