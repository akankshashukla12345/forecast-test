# SF Expense Analytics & Forecast Dashboard

This repository contains the data analysis and forecasting scripts for the **SF Main Expense Data** analytics dashboard.

## Overview

The scripts process expense data from the SF Main Expense Data Google Sheet, providing:

- **Monthly & Quarterly breakdowns** of recognized spend and funding amounts
- **Historical trend analysis** from 2018 through 2026
- **Forecasting** for current (2026) and upcoming years (2027+)
- **Pillar-level breakdowns** across Entertainment, Games, Developer Ecosystem, 1P Studios, and more
- **Accounting treatment analysis** (Opex vs. Capex)
- **Pipeline status summaries** (Committed, Closed, Pending Contract, etc.)

## Files

| File | Description |
|------|-------------|
| `analyze_expenses.py` | Loads raw data from all sheet chunks, cleans and parses dates/currencies, computes monthly and quarterly aggregations by pillar, accounting treatment, and pipeline status |
| `compute_forecast.py` | Builds forecast series, YoY growth rates, and prepares structured JSON output for the interactive dashboard |

## Data Source

- **Sheet**: SF Main Expense Data
- **Spreadsheet ID**: `1K-Hh6SUo5OHbLbqCNwy9V04d97IfgnlnjeX8NanQVyw`
- **Records**: ~14,307 rows with spend recognition dates
- **Date Range**: December 2018 – February 2030

## Key Metrics (2024–2026)

| Year | Recognized Spend | YoY Growth |
|------|-----------------|------------|
| 2023 | $180M | — |
| 2024 | $471M | +161% |
| 2025 | $655M | +39% |
| 2026 | $447M (YTD + committed) | — |

## Requirements

```bash
pip install pandas numpy
```

## Usage

```bash
# Step 1: Analyze and aggregate the raw data
python analyze_expenses.py

# Step 2: Compute forecasts and prepare dashboard data
python compute_forecast.py
```

## Output

Both scripts produce JSON files consumed by the interactive HTML dashboard:
- `expense_analysis.json` — aggregated monthly/quarterly/yearly data
- `expense_dashboard/dashboard_data.json` — forecast-ready data for visualization
