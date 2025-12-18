"""Airflow DAG scaffold for the London Air Quality + Weather lakehouse."""
from datetime import datetime

from airflow import DAG


def build_dag() -> DAG:
    with DAG(
        dag_id="aqw_london_lakehouse",
        start_date=datetime(2024, 1, 1),
        schedule=None,
        catchup=False,
        tags=["aqw", "lakehouse"],
    ) as dag:
        # TODO: define extract -> land -> load -> transform tasks
        pass

    return dag


dag = build_dag()
