from airflow import DAG
from airflow.operators.python import PythonOperator

from datetime import datetime, timedelta
from src.producers import produce_initializetion_matches

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

    initialize_matches = PythonOperator(
        task_id='initialize_matches',
        python_callable=produce_initializetion_matches
    )