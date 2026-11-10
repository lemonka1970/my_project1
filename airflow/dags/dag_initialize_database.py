from airflow import DAG
from airflow.operators.python import PythonOperator

from datetime import datetime, timedelta
from src.database.postgres.initializetion import initialize_db_postgres
from src.database.clickhouse.initializetion import initializetion_row_tables

default_args = {
    'start_date': datetime(2020, 1, 1),
    'retries': 3,
    'retry_delay': timedelta(seconds=5)
}

with DAG(
    dag_id = 'initialize_database',
    schedule_interval=None,
    catchup=False,
    default_args=default_args
) as dag:


    initialize_postgres_db = PythonOperator(
        task_id = 'initialize_postgres_db',
        python_callable = initialize_db_postgres
    )

    initialize_clickhouse_row = PythonOperator(
        task_id = 'initialize_clickhouse_row',
        python_callable = initializetion_row_tables
    )

    [initialize_postgres_db, initialize_clickhouse_row]