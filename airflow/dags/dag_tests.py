from airflow import DAG
from airflow.operators.python import PythonOperator

from datetime import datetime, timedelta

from src.sync_table_to_clickhouse import sync_table_to_clichouse


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

    regions = PythonOperator(
        task_id = 'sync_table_reigons',
        python_callable = sync_table_to_clichouse,
        op_args = ['regions', ['region_id', 'region_name'], 'region_id', 'initialize']
    )

    seasons = PythonOperator(
        task_id = 'sync_table_seasons',
        python_callable = sync_table_to_clichouse,
        op_args = ['seasons', ['season_id', 'start_date', 'end_date', 'is_current', 'league_id'], 'season_id', 'initialize']
    )

    regions >> seasons