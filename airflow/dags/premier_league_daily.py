import os
from datetime import datetime, timedelta

import requests
from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG

SEASON = os.getenv("PL_SEASON", "2025")
PROJECT = "/opt/airflow/project"
DBT = "/opt/airflow/dbt_venv/bin/dbt"


def notify_failure(context):
    """Runs when a task fails after all its retries."""
    ti = context["task_instance"]
    message = f"Pipeline failed: dag={ti.dag_id} task={ti.task_id}"
    print(message)
    webhook = os.getenv("SLACK_WEBHOOK_URL")
    if webhook:
        requests.post(webhook, json={"text": message}, timeout=10)


default_args = {
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": notify_failure,
}

with DAG(
    dag_id="premier_league_daily",
    description="Fetch, load, transform and test Premier League data",
    start_date=datetime(2026, 10, 1),
    schedule="@daily",
    catchup=False,
    default_args=default_args,
    tags=["premier-league"],
) as dag:

    fetch_matches = BashOperator(
        task_id="fetch_matches",
        bash_command=f"cd {PROJECT} && python ingest/fetch_matches.py --season {SEASON}",
    )

    load_to_postgres = BashOperator(
        task_id="load_to_postgres",
        bash_command=f"cd {PROJECT} && python ingest/load_matches.py --season {SEASON}",
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd {PROJECT}/dbt_project && {DBT} run --profiles-dir .",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd {PROJECT}/dbt_project && {DBT} test --profiles-dir .",
    )

    fetch_matches >> load_to_postgres >> dbt_run >> dbt_test
