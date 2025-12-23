from __future__ import annotations

import os
from airflow.decorators import dag, task
from airflow.utils.dates import days_ago
from airflow.operators.python import get_current_context

from aqw.openaq_client import list_locations_near, sensor_hourly
from aqw.lake import put_json, s3_client
from aqw.warehouse import upsert_air_quality

LONDON_LAT, LONDON_LON = 51.5074, -0.1278

@dag(
    schedule="@hourly",
    start_date=days_ago(1),
    catchup=False,
    tags=["portfolio", "openaq", "open-meteo", "lakehouse"],
)
def aqw_london_lakehouse():
    @task
    def discover_sensors() -> list[dict]:
        # Find nearby locations, then select a subset of sensors
        locations = list_locations_near(LONDON_LAT, LONDON_LON, radius_m=8000, limit=10)
        sensors = []
        for loc in locations:
            for s in loc.get("sensors", []):
                sensors.append({
                    "location_id": loc.get("id"),
                    "location_name": loc.get("name"),
                    "latitude": (loc.get("coordinates") or {}).get("latitude"),
                    "longitude": (loc.get("coordinates") or {}).get("longitude"),
                    "sensor_id": s["id"],
                    "parameter": (s.get("parameter") or {}).get("name"),
                    "units": (s.get("parameter") or {}).get("units"),
                })
        # Keep it bounded for a free-tier friendly demo
        return sensors[:25]

    @task
    def extract_and_land(sensors: list[dict]) -> dict:
        ctx = get_current_context()
        start = ctx["data_interval_start"].in_timezone("UTC")
        end = ctx["data_interval_end"].in_timezone("UTC")

        bucket = os.getenv("LAKE_BUCKET", "lake")
        # Ensure bucket exists (idempotent)
        s3 = s3_client()
        try:
            s3.head_bucket(Bucket=bucket)
        except Exception:
            s3.create_bucket(Bucket=bucket)

        all_rows = []
        for s in sensors:
            results = sensor_hourly(
                s["sensor_id"],
                datetime_from=start.to_iso8601_string(),
                datetime_to=end.to_iso8601_string(),
                limit=1000,
            )

            # Land raw
            key = f"raw/openaq/hourly/{start.format('YYYY/MM/DD/HH')}/sensor_id={s['sensor_id']}.json"
            put_json(bucket, key, {"sensor": s, "data_interval": [str(start), str(end)], "results": results})

            # Flatten for warehouse
            for r in results:
                all_rows.append({
                    "sensor_id": s["sensor_id"],
                    "location_id": s.get("location_id"),
                    "location_name": s.get("location_name"),
                    "parameter": s.get("parameter") or "unknown",
                    "units": s.get("units"),
                    "latitude": s.get("latitude"),
                    "longitude": s.get("longitude"),
                    "ts_utc": r.get("datetime") or r.get("datetimeTo", {}).get("utc"),
                    "value": r.get("value") or r.get("avg"),
                })

        inserted = upsert_air_quality(all_rows)
        return {"window": [str(start), str(end)], "rows_upserted": inserted}

    sensors = discover_sensors()
    extract_and_land(sensors)

aqw_london_lakehouse()
