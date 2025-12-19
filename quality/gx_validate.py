import os
import great_expectations as gx


def run():
    context = gx.get_context()

    # Add a Postgres datasource in code (you can later move this to config files)
    datasource = context.sources.add_postgres(
        name="warehouse",
        connection_string=(
            f"postgresql+psycopg2://{os.environ['WAREHOUSE_USER']}:{os.environ['WAREHOUSE_PASSWORD']}"
            f"@{os.environ['WAREHOUSE_HOST']}:{os.environ['WAREHOUSE_PORT']}/{os.environ['WAREHOUSE_DB']}"
        ),
    )

    asset = datasource.add_table_asset(
        name="fct_air_quality_hourly",
        table_name="fct_air_quality_hourly",
        schema_name="marts",
    )
    batch_request = asset.build_batch_request()

    suite = context.add_or_update_expectation_suite(expectation_suite_name="aqw_basic_suite")
    validator = context.get_validator(batch_request=batch_request, expectation_suite=suite)

    validator.expect_column_values_to_not_be_null("sensor_id")
    validator.expect_column_values_to_not_be_null("ts_utc")
    validator.expect_column_values_to_be_between("value", min_value=0, max_value=1000)  # adjust per pollutant/units

    results = validator.validate()
    if not results["success"]:
        raise SystemExit("GX validation failed")


if __name__ == "__main__":
    run()
