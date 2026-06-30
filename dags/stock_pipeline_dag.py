from datetime import datetime, timedelta
import sys

sys.path.insert(0, "/opt/airflow")

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.standard.operators.bash import BashOperator

from ingestion.fetch_prices import get_all_symbols, fetch_prices_batched, save_raw
from loading.load_to_postgres import get_engine, create_raw_table, upsert_prices


def run_ingestion():
    symbols = get_all_symbols()
    print(f"Fetching {len(symbols)} symbols")
    long_df = fetch_prices_batched(symbols, batch_size=50, delay=2)
    save_raw(long_df)


def run_load():
    import pandas as pd
    from datetime import date
    today = date.today().isoformat()
    df = pd.read_csv(f"/opt/airflow/data/raw/{today}/prices.csv")
    engine = get_engine()
    create_raw_table(engine)
    upsert_prices(df, engine)


default_args = {
    "owner": "daksh",
    "retries": 2,
}

with DAG(
    dag_id="stock_pipeline_dag",
    default_args=default_args,
    schedule="@daily",
    start_date=datetime(2026, 6, 1),
    catchup=False,
    tags=["stocks", "portfolio-project"],
) as dag:

    fetch_and_save = PythonOperator(
        task_id="fetch_and_save_prices",
        python_callable=run_ingestion,
        execution_timeout=timedelta(minutes=30),
    )

    load_to_postgres = PythonOperator(
        task_id="load_to_postgres",
        python_callable=run_load,
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command="cd /opt/airflow/dbt_project && dbt run",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command="cd /opt/airflow/dbt_project && dbt test",
    )

    fetch_and_save >> load_to_postgres >> dbt_run >> dbt_test
