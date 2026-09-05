# Air Quality Prediction using an End-to-End Data Pipeline and Explainable Machine Learning

Predicting AQI for data-scarce Kathmandu, and using SHAP to explain what drives AQI spikes (traffic, weather, seasonal burning) - not just forecasting the numbers.

## Project Overview

This project builds a full pipeline: data ingestion → cleaning → feature engineering → model training → SHAP explainability → dashboard. Data is pulled from [OpenAQ](https://openaq.org), using Kathmandu Metropolitan City's Clarity Node-S sensor stations.

## Ingestion Pipeline Logic

The basic idea is:

OpenAQ
   │
   ▼
Monitoring Location
   │
   ▼
Find available sensors
   │
   ▼
Download measurements
   │
   │  (one year at a time)
   ▼
Combine all measurements
   │
   ▼
Reshape into a table
   │
   ▼
Save as CSV

## Data Sources — OpenAQ Location IDs

| Station | Location ID |
|---|---|
| Tankeshwor | 6093550 |
| Teku | 6093551 |
| Mid Baneshwor | 6142022 |
| Tripureshwor | 6176215 |

## Project Structure

```
air-quality-etl-ml-pipeline/
├── air_venv/              # virtual environment (not committed)
├── .env                   # API keys (not committed)
├── data/
│   ├── raw/                # raw pulls from OpenAQ (not committed)
│   └── processed/          # cleaned/merged data (not committed)
├── src/
│   └── ingestion/
│       └── openaq_pipeline.py
├── requirements.txt
├──README.md
└──.gitignore
```

## Setup

1. Create and activate a virtual environment, then install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Get a free API key from [explore.openaq.org](https://explore.openaq.org) (sign up → account → API keys).

3. Create a `.env` file in the project root:
   ```
   OPENAQ_API_KEY=your_actual_key_here
   ```

## Running the Pipeline

Pull historical data for one station:

```bash
python src/ingestion/openaq_pipeline.py --location_id <ID> --start 2017-01-01 --end 2025-12-31 --out data/raw/<station_name>.csv
```

Example — Tankeshwor:
```bash
python src/ingestion/openaq_pipeline.py --location_id 6093550 --start 2017-01-01 --end 2025-12-31 --out data/raw/tankeshwor.csv
```

Run once per station, changing `--location_id` and `--out` each time.

> Tip: test with a short date range first (e.g. 2 weeks) to confirm the `location_id` is correct before running the full historical pull.

## Commit Convention

This project follows [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix | Use for |
|---|---|
| `feat:` | New functionality (new script, new pipeline stage, new feature) |
| `fix:` | Bug fixes |
| `chore:` | Setup/maintenance (dependencies, folder structure, config) |
| `docs:` | README or documentation-only changes |
| `refactor:` | Restructuring code without changing behavior |
| `data:` | Dataset-related changes (schema changes, new data source) |
| `test:` | Adding/updating tests |
