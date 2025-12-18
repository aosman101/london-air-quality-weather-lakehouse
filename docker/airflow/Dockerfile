# TODO: customize Airflow image for the lakehouse project
FROM apache/airflow:2.7.3

# Example: install extra providers or system packages
# USER root
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential \
#     && rm -rf /var/lib/apt/lists/*
# USER airflow

COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt
