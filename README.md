An end-to-end data engineering project that ingests daily stock price data for all NSE-listed companies (~2,374 tickers), transforms it using dbt, and serves it through an interactive dashboard — fully orchestrated with Apache Airflow and containerized with Docker.


## Architecture

yfinance API → Batched Ingestion → Raw CSV → Postgres (raw layer)

↓

dbt (staging → marts)

↓

Airflow (daily orchestration)

↓

Streamlit Dashboard

## Tech Stack

- **Ingestion**: Python, yfinance (batched, ~2,374 NSE tickers)
- **Storage**: PostgreSQL (raw + transformed layers)
- **Transformation**: dbt (staging models, fact tables, window functions)
- **Orchestration**: Apache Airflow (daily DAG, retries, data quality tests)
- **Dashboard**: Streamlit (top gainers/losers, ticker detail, rolling averages)
- **Infrastructure**: Docker + Docker Compose (fully containerized)

## What the pipeline does

1. Fetches the full NSE-listed equity universe from NSE's public CSV
2. Downloads daily OHLCV price data in batches of 50 tickers (rate-limit safe)
3. Saves raw data as immutable dated CSV files
4. Loads into Postgres with idempotent upserts (safe to rerun)
5. dbt models clean and transform raw data into analytical tables including daily returns and 7-day rolling averages
6. dbt tests validate data quality on every run
7. Airflow orchestrates the whole pipeline on a daily schedule
8. Streamlit dashboard reads from the transformed tables

## Running locally

### Prerequisites
- Docker Desktop

### Steps

```bash
# Clone the repo
git clone https://github.com/daksh1293/Stock-Data-Pipeline.git
cd Stock-Data-Pipeline

# Set up environment
echo "AIRFLOW_UID=$(id -u)" > .env_airflow

# Initialize Airflow
docker compose --env-file .env_airflow up airflow-init

# Start everything
docker compose --env-file .env_airflow up -d

# Trigger the pipeline (first run)
# Go to http://localhost:8081 → login: airflow/airflow → trigger stock_pipeline_dag

# View the dashboard
# Go to http://localhost:8501
```

### Ports
- **Airflow UI**: http://localhost:8081 (login: airflow / airflow)
- **Dashboard**: http://localhost:8501

## Data freshness

The pipeline runs daily at midnight. Data updates automatically as long as Docker is running. On first run, trigger the DAG manually to populate the database before viewing the dashboard.

## Project structure

```
Stock-Data-Pipeline/
├── ingestion/
│   ├── fetch_tickers.py       # Downloads the NSE equity list CSV
│   └── fetch_prices.py        # Fetches price data from yfinance in batches
├── loading/
│   └── load_to_postgres.py    # Reads raw CSV and upserts rows into Postgres
├── dbt_project/
│   ├── models/
│   │   ├── staging/
│   │   │   ├── sources.yml           # Tells dbt where the raw table is
│   │   │   └── stg_stock_prices.sql  # Light cleaning of raw data
│   │   └── marts/
│   │       └── fct_daily_returns.sql # Window functions: returns, rolling avg
│   └── dbt_project.yml        # dbt project config
├── dags/
│   └── stock_pipeline_dag.py  # Airflow DAG: task order and schedule
├── dashboard/
│   └── app.py                 # Streamlit dashboard
├── Dockerfile                 # Extends Airflow image with project dependencies
├── docker-compose.yaml        # All services: Airflow, Postgres, dashboard
├── requirements.txt           # Python packages for Docker image
└── README.md
```