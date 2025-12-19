{{ config(materialized="incremental", unique_key=["sensor_id", "ts_utc"]) }}

select
  sensor_id,
  location_id,
  location_name,
  parameter,
  units,
  latitude,
  longitude,
  ts_utc,
  value
from {{ ref("stg_air_quality_hourly") }}

{% if is_incremental() %}
  -- only process new rows since the latest ts_utc already in this model
  where ts_utc > (select coalesce(max(ts_utc), '1970-01-01') from {{ this }})
{% endif %}
