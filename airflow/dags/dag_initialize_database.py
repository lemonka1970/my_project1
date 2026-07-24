from airflow import DAG
from airflow.operators.python import PythonOperator

from datetime import datetime, timedelta
from src.database import (initialize_database)

default_args = {
    'start_date': datetime(2020, 1, 1),
    'retries': 3,
    'retry_delay': timedelta(minutes=1)
}

with DAG(
    dag_id = 'initialize_database',
    schedule_interval=None,
    catchup=False,
    default_args=default_args
) as dag:
    initialize_database = PythonOperator(
        task_id = 'initialize_database',
        python_callable = initialize_database
    )