
FROM apache/airflow:2.9.3
 
USER root
 
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    librdkafka-dev \
    gcc \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
 
USER airflow
 
ARG AIRFLOW_VERSION=2.9.3
ARG PYTHON_VERSION=3.12
 
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"
 
