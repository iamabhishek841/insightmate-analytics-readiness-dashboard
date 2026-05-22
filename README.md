# InsightMate — Analytics Readiness & Data Quality Decision Dashboard

InsightMate is a Business Analytics coursework-inspired dashboard that helps students and analysts decide whether a CSV dataset is ready for analysis, reporting, or modelling.

It is designed to go beyond a simple chart dashboard. The app diagnoses data quality risks, ranks risky columns, checks modelling readiness, suggests next actions, and exports a structured readiness report.

## Features

- CSV upload and automated dataset profiling
- Missing value analysis
- Duplicate row detection
- Column type inference
- Constant and near-constant column detection
- High-cardinality categorical field detection
- IQR-based outlier detection
- Rule-based data quality score
- Column risk ranking
- Target-based modelling readiness check
- Classification/regression task suggestion
- Target imbalance warning for classification tasks
- Correlation analysis and relationship mapping
- Leakage-risk heuristic for target-related features
- Cleaning action plan
- Downloadable readiness report
- Review history for current session
- Basic backend tests

## Tech Stack

- Python
- Streamlit
- Pandas
- NumPy
- Plotly
- FastAPI optional backend
- SQLite optional persistence layer
- Pytest

## Project Structure

```text
insightmate/
├── app.py
├── api.py
├── requirements.txt
├── README.md
├── core/
│   ├── __init__.py
│   ├── profiler.py
│   ├── scoring.py
│   ├── readiness.py
│   ├── recommendations.py
│   ├── reporting.py
│   └── storage.py
├── sample_data/
│   └── sample_customer_data.csv
├── tests/
│   └── test_core.py
└── .streamlit/
    └── config.toml
```

## How to Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Optional FastAPI Run

The Streamlit app works directly without FastAPI. `api.py` is included to show API-first design.

```bash
uvicorn api:app --reload
```

## Streamlit Cloud Deployment

1. Upload this project to a GitHub repository.
2. Go to Streamlit Community Cloud.
3. Create a new app.
4. Select the GitHub repository.
5. Set the main file path as:

```text
app.py
```

6. Deploy.

## Suggested Resume Bullet

```text
Built a Business Analytics decision dashboard using Python, Streamlit, Pandas, and rule-based scoring to assess whether messy CSV datasets are ready for analysis, reporting, or modelling.
```

## Coursework Context

This project was designed for Business Analytics coursework workflows where students often need to inspect messy datasets before modelling, reporting, or presenting insights. The dashboard turns manual dataset checking into a structured analytics-readiness decision process.
