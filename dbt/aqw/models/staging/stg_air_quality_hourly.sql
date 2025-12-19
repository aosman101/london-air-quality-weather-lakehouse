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
from raw.air_quality_hourly
where ts_utc is not null
