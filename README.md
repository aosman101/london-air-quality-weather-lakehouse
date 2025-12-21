# London Air Quality + Weather Lakehouse (Airflow / dbt / Postgres / MinIO / Metabase)

[![CI](https://github.com/aosman101/london-air-quality-weather-lakehouse/actions/workflows/ci.yml/badge.svg)](https://github.com/aosman101/london-air-quality-weather-lakehouse/actions/workflows/ci.yml)
![Airflow](https://img.shields.io/badge/Airflow-2.7-017CEE?logo=apacheairflow&logoColor=white)
![dbt](https://img.shields.io/badge/dbt-Core-FE5C3A?logo=dbt&logoColor=white)
![Postgres](https://img.shields.io/badge/Postgres-15-336791?logo=postgresql&logoColor=white)
![MinIO](https://img.shields.io/badge/MinIO-S3%20lake-FF4F00?logo=minio&logoColor=white)
![Metabase](https://img.shields.io/badge/Metabase-BI-509EE3?logo=metabase&logoColor=white)
![Great Expectations](https://img.shields.io/badge/Great%20Expectations-Data%20Quality-5C4EE5)

Local lakehouse demo that pulls hourly OpenAQ readings around London, lands raw JSON in a MinIO lake, upserts flattened rows into Postgres, transforms with dbt, and runs Great Expectations checks before exploring in Metabase. Everything is containerized for quick spin-up.

> Portfolio / learning project; the Airflow Compose stack is intentionally minimal and not production hardened.

---

## System architecture

```
      +------------------+          +-------------------+
      |   OpenAQ API      |          |   Open-Meteo API   |
      +---------+---------+          +---------+---------+
                |                              |
                v                              v
         +------+-------------------------------+------+
         |                Apache Airflow               |
         |  DAG: extract -> land -> load -> transform  |
         +------+-------------------------------+------+
                |                              |
                v                              v
      +------------------+          +-------------------+
      |  MinIO (S3 lake) |          | Postgres (warehouse)|
      | raw JSON objects |          | raw/stg/marts tables|
      +---------+--------+          +---------+----------+
                |                              |
                +---------------+--------------+
                                v
                           +----+----+
                           | Metabase|
                           +---------+

```

- `dags/aqw_london_lakehouse.py` discovers nearby sensors, pulls the last hour of readings, writes raw objects to S3-compatible storage, and idempotently upserts into `raw.air_quality_hourly`.
- `dbt/aqw` materializes staging + fact models; the fact is incremental on `(sensor_id, ts_utc)`.
- `quality/gx_validate.py` runs a basic suite against `marts.fct_air_quality_hourly`.

---

## Stack (local, via Docker Compose)
- Airflow webserver + scheduler (LocalExecutor) at `localhost:8080`
- Postgres (warehouse) at `localhost:5434`
- MinIO API/console at `localhost:9000/9001`
- Metabase at `localhost:3000`
- Supporting Postgres for Airflow metadata at `localhost:5433`

---

## Quickstart

1) Prerequisites  
Docker + Docker Compose, plus a free `OPENAQ_API_KEY` from OpenAQ.

2) Create `.env`  
Place this next to `docker/compose.yaml`:
```
OPENAQ_API_KEY=your_token
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=change_me
WAREHOUSE_PASSWORD=change_me
# Optional overrides
WAREHOUSE_HOST=warehouse-db
WAREHOUSE_PORT=5432
WAREHOUSE_DB=warehouse
WAREHOUSE_USER=warehouse
```

3) Bring up the stack  
```bash
docker compose -f docker/compose.yaml up -d --build
```

4) Create an Airflow admin user (first run only)  
```bash
docker compose -f docker/compose.yaml run --rm airflow-webserver \
  airflow users create --username admin --password admin \
  --firstname Air --lastname Flow --role Admin --email admin@example.com
```

5) Use Airflow  
- Open http://localhost:8080, enable DAG `aqw_london_lakehouse`, trigger a run.
- Raw objects land under `raw/openaq/hourly/...` in MinIO (console: http://localhost:9001).
- Flattened rows upsert into `raw.air_quality_hourly` in Postgres (`localhost:5434` from your host).

6) Run dbt transforms  
```bash
cd dbt/aqw
dbt deps
dbt run
```
`profiles.yml` points to the warehouse on `localhost:5434` with schema `marts`.

7) Data quality check (optional)  
```bash
export WAREHOUSE_USER=warehouse WAREHOUSE_PASSWORD=... WAREHOUSE_HOST=localhost WAREHOUSE_PORT=5434 WAREHOUSE_DB=warehouse
python quality/gx_validate.py
```

8) Explore in Metabase  
Connect to Postgres at `localhost:5434`, database `warehouse`, user `warehouse`.

To tear down: `docker compose -f docker/compose.yaml down -v`

---

## Data + models
- Raw landing: `raw.air_quality_hourly` (hourly sensor readings; primary key `(sensor_id, ts_utc)`).
- Transform: `dbt/aqw/models/staging/stg_air_quality_hourly.sql` → `dbt/aqw/models/marts/fct_air_quality_hourly.sql` (incremental).
- Quality: `quality/gx_validate.py` checks sensor + timestamp presence and bounds `value`.

---

## Configuration knobs
- `OPENAQ_API_KEY` (required) — OpenAQ auth token.
- `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` — MinIO credentials; `LAKE_BUCKET` defaults to `lake`.
- `WAREHOUSE_*` — connection info for the warehouse database (used by Airflow, dbt, GX).
- `MINIO_ENDPOINT` / `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` — passed into Airflow for S3 access.

---

## Extending / next steps
- Add Open-Meteo pulls into the DAG and populate `raw.weather_hourly` (schema already provisioned).
- Layer more dbt models (dimensions, rollups) and dbt tests.
- Harden Airflow for production (remote executor, secrets backend, auth).
- Add CI checks for dbt + GX and smoke tests for the DAG.

---

## Project layout
```
.
├── dags/                 Airflow DAGs (TaskFlow)
├── dbt/aqw/              dbt project (models, profiles.yml)
│   ├── models/staging/   staging models
│   └── models/marts/     fact models
├── quality/              Great Expectations entrypoint
├── src/aqw/              Python clients (OpenAQ, lake, warehouse)
└── docker/               Docker Compose + Airflow image build
```

---

## References
- Airflow TaskFlow tutorial: https://airflow.apache.org/docs/apache-airflow/stable/tutorial/taskflow.html
- OpenAQ API: https://docs.openaq.org/
- Open-Meteo API: https://open-meteo.com/en/docs
- Metabase on Docker: https://www.metabase.com/docs/latest/installation-and-operation/running-metabase-on-docker
