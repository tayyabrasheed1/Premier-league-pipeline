FROM apache/airflow:3.3.1

RUN pip install --no-cache-dir requests python-dotenv psycopg2-binary

RUN python -m venv /opt/airflow/dbt_venv \
 && /opt/airflow/dbt_venv/bin/pip install --no-cache-dir dbt-postgres
