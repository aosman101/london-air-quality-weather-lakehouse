# London Air Quality + Weather Lakehouse (Airflow / dbt / Postgres / MinIO / Metabase)

[![CI](https://github.com/aosman101/london-air-quality-weather-lakehouse/actions/workflows/ci.yml/badge.svg)](https://github.com/aosman101/london-air-quality-weather-lakehouse/actions/workflows/ci.yml)
![Airflow](https://img.shields.io/badge/Airflow-2.7-017CEE?logo=apacheairflow&logoColor=white)
![dbt](https://img.shields.io/badge/dbt-Core-FE5C3A?logo=dbt&logoColor=white)
![Postgres](https://img.shields.io/badge/Postgres-15-336791?logo=postgresql&logoColor=white)
![MinIO](https://img.shields.io/badge/MinIO-S3%20lake-FF4F00?logo=minio&logoColor=white)
![Metabase](https://img.shields.io/badge/Metabase-BI-509EE3?logo=metabase&logoColor=white)
![Great Expectations](https://img.shields.io/badge/Great%20Expectations-Data%20Quality-5C4EE5)

Hands-on lakehouse demo for London air quality and weather:
- Pull OpenAQ hourly sensor readings (and optionally Open-Meteo weather).
- Land raw JSON in a MinIO data lake, upsert flattened rows into Postgres.
- Transform with dbt (incremental models) and validate with Great Expectations.
- Explore downstream in Metabase. Entire stack runs locally via Docker Compose.

> This is a learning/portfolio project. The Docker Compose Airflow setup is for local use, not production.

---

## Architecture at a glance

```
OpenAQ API        Open-Meteo API
    |                   |
    v                   v
           Apache Airflow DAG
     (extract -> land -> load -> transform)
                |                   |
                v                   v
         MinIO (S3 lake)     Postgres warehouse
       raw JSON objects      raw / staging / marts
                \                 /
                 \               /
                     Metabase BI
```

---

## What is included
- Airflow TaskFlow DAG: discover nearby sensors, fetch hourly readings, write lake objects, upsert into warehouse.
- dbt models: staging and fact (`raw.air_quality_hourly` -> `marts.fct_air_quality_hourly`) with incremental materialization.
- Great Expectations: simple checks on the fact model (`quality/gx_validate.py`).
- Dockerized stack: Postgres (airflow + warehouse), MinIO, Metabase, Airflow webserver and scheduler.

---

## Quickstart (local)

1) Prerequisites  
Docker + Docker Compose, and a free `OPENAQ_API_KEY`.

2) Configure env vars  
Copy `.env.example` to `.env` and set at least:
```
OPENAQ_API_KEY=...
MINIO_ROOT_USER=...
MINIO_ROOT_PASSWORD=...
WAREHOUSE_PASSWORD=...
```

3) Bring up the stack  
```bash
docker compose -f docker/compose.yaml up -d --build
```

4) Use Airflow  
- Open http://localhost:8080, enable the DAG `aqw_london_lakehouse`, and trigger a run.
- Lake objects land under `raw/openaq/hourly/...` in MinIO (console: http://localhost:9001).
- Flattened rows upsert into `raw.air_quality_hourly` in Postgres (`localhost:5434` by default).

5) Run dbt transforms  
```bash
cd dbt/aqw
dbt deps
dbt parse
dbt run
```
The profile at `dbt/aqw/profiles.yml` defaults to `localhost:5434` and schema `marts`.

6) Data quality check (optional)  
```bash
export WAREHOUSE_USER=warehouse WAREHOUSE_PASSWORD=... WAREHOUSE_HOST=localhost WAREHOUSE_PORT=5434 WAREHOUSE_DB=warehouse
python quality/gx_validate.py
```

7) Explore in Metabase  
Connect to Postgres at `localhost:5434`, database `warehouse`, user `warehouse`.

---

## Environment variables (key ones)
- `OPENAQ_API_KEY` (required) - OpenAQ auth token.
- `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` - MinIO credentials.
- `WAREHOUSE_PASSWORD` (and optionally `WAREHOUSE_HOST/PORT/DB/USER`) - Postgres warehouse auth.
- `LAKE_BUCKET` - defaults to `lake` when writing to MinIO.

---

## Project layout
```
dags/                   Airflow DAGs
dbt/aqw/                dbt project (models, profile)
quality/gx_validate.py  Great Expectations entrypoint
src/aqw/                Python clients (OpenAQ, lake, warehouse)
docker/                 Docker Compose and Airflow image build
```

---

## References
- Airflow TaskFlow tutorial: https://airflow.apache.org/docs/apache-airflow/stable/tutorial/taskflow.html
- OpenAQ API: https://docs.openaq.org/
- Open-Meteo API: https://open-meteo.com/en/docs
- Metabase on Docker: https://www.metabase.com/docs/latest/installation-and-operation/running-metabase-on-docker
