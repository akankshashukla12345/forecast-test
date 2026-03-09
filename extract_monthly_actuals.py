import json
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Load all data chunks
all_rows = []
with open('/home/ubuntu/sf_expense_data.json') as f:
    d = json.load(f)
rows = d.get('values', [])
headers = rows[0]
all_rows.extend(rows[1:])

for i in range(2, 7):
    try:
        with open(f'/home/ubuntu/sf_expense_data{i}.json') as f:
            d = json.load(f)
        rows = d.get('values', [])
        if rows:
            all_rows.extend(rows)
    except FileNotFoundError:
        break

# Build DataFrame
padded_rows = []
for row in all_rows:
    if len(row) < len(headers):
        row = row + [''] * (len(headers) - len(row))
    padded_rows.append(row[:len(headers)])

df = pd.DataFrame(padded_rows, columns=headers)

def parse_currency(val):
    if pd.isna(val) or val == '' or val is None:
        return 0.0
    val = str(val).replace('$', '').replace(',', '').strip()
    try:
        return float(val)
    except:
        return 0.0

def parse_date(val):
    if pd.isna(val) or val == '' or val is None:
        return pd.NaT
    for fmt in ['%m/%d/%Y', '%Y-%m-%d', '%m/%d/%y']:
        try:
            return pd.to_datetime(val, format=fmt)
        except:
            pass
    try:
        return pd.to_datetime(val)
    except:
        return pd.NaT

df['Recognized_Amount'] = df['Recognized Amount'].apply(parse_currency)
df['Funding_Amount'] = df['Funding: Funding Amount'].apply(parse_currency)
df['Spend_Date'] = df['Spend Recognition Date'].apply(parse_date)
df['Is_Actual_Raw'] = df['Actual?'].apply(parse_currency)

df_dated = df[df['Spend_Date'].notna()].copy()
df_dated['Year'] = df_dated['Spend_Date'].dt.year
df_dated['Month'] = df_dated['Spend_Date'].dt.month
df_dated['Quarter'] = df_dated['Spend_Date'].dt.quarter

# -------------------------------------------------------
# UNDERSTANDING "Actual?" COLUMN
# -------------------------------------------------------
print("=== 'Actual?' column unique values ===")
print(df['Actual?'].value_counts().head(20))
print()

# -------------------------------------------------------
# 2025 FULL YEAR MONTHLY ACTUALS
# -------------------------------------------------------
df_2025 = df_dated[df_dated['Year'] == 2025].copy()
monthly_2025 = df_2025.groupby('Month').agg(
    Recognized=('Recognized_Amount', 'sum'),
    Funding=('Funding_Amount', 'sum'),
    Count=('Recognized_Amount', 'count')
).reset_index().sort_values('Month')

print("=== 2025 Monthly Actuals ===")
months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
for _, row in monthly_2025.iterrows():
    print(f"  {months[int(row['Month'])-1]} 2025: Recognized=${row['Recognized']:>15,.0f}  |  Count={row['Count']}")

total_2025 = monthly_2025['Recognized'].sum()
print(f"\n  TOTAL 2025: ${total_2025:,.0f}")

# -------------------------------------------------------
# 2026 MONTHLY — ALL RECORDS (actual + committed/forecast)
# -------------------------------------------------------
df_2026 = df_dated[df_dated['Year'] == 2026].copy()
monthly_2026_all = df_2026.groupby('Month').agg(
    Recognized=('Recognized_Amount', 'sum'),
    Funding=('Funding_Amount', 'sum'),
    Count=('Recognized_Amount', 'count')
).reset_index().sort_values('Month')

print("\n=== 2026 Monthly — All Records ===")
for _, row in monthly_2026_all.iterrows():
    print(f"  {months[int(row['Month'])-1]} 2026: Recognized=${row['Recognized']:>15,.0f}  |  Count={row['Count']}")

# -------------------------------------------------------
# 2026 ACTUALS ONLY (Actual? = $1 or non-zero)
# -------------------------------------------------------
# Check what "Actual?" = 1 means
df_2026_actual = df_2026[df_2026['Is_Actual_Raw'] > 0].copy()
monthly_2026_actual = df_2026_actual.groupby('Month').agg(
    Recognized=('Recognized_Amount', 'sum'),
    Count=('Recognized_Amount', 'count')
).reset_index().sort_values('Month')

print("\n=== 2026 Monthly — Actuals Only (Actual? > 0) ===")
for _, row in monthly_2026_actual.iterrows():
    print(f"  {months[int(row['Month'])-1]} 2026: Recognized=${row['Recognized']:>15,.0f}  |  Count={row['Count']}")

# -------------------------------------------------------
# PIPELINE STATUS for 2026 by month
# -------------------------------------------------------
print("\n=== 2026 Monthly by Pipeline Status ===")
status_monthly_2026 = df_2026.groupby(['Month', 'Funding: Pipeline Status']).agg(
    Recognized=('Recognized_Amount', 'sum'),
    Count=('Recognized_Amount', 'count')
).reset_index()

for month in range(1, 13):
    month_data = status_monthly_2026[status_monthly_2026['Month'] == month]
    if not month_data.empty:
        total = month_data['Recognized'].sum()
        print(f"\n  {months[month-1]} 2026 (Total: ${total:,.0f}):")
        for _, row in month_data.iterrows():
            print(f"    [{row['Funding: Pipeline Status']:20s}] ${row['Recognized']:>12,.0f}  ({row['Count']} records)")

# -------------------------------------------------------
# Jan & Feb 2026 DEEP DIVE
# -------------------------------------------------------
print("\n\n=== JAN 2026 DETAIL ===")
df_jan26 = df_2026[df_2026['Month'] == 1]
print(f"Total records: {len(df_jan26)}")
print(f"Total Recognized: ${df_jan26['Recognized_Amount'].sum():,.0f}")
print(f"Actual? distribution: {df_jan26['Actual?'].value_counts().to_dict()}")
print(f"Status distribution: {df_jan26['Funding: Pipeline Status'].value_counts().to_dict()}")

print("\n=== FEB 2026 DETAIL ===")
df_feb26 = df_2026[df_2026['Month'] == 2]
print(f"Total records: {len(df_feb26)}")
print(f"Total Recognized: ${df_feb26['Recognized_Amount'].sum():,.0f}")
print(f"Actual? distribution: {df_feb26['Actual?'].value_counts().to_dict()}")
print(f"Status distribution: {df_feb26['Funding: Pipeline Status'].value_counts().to_dict()}")

# -------------------------------------------------------
# SAVE CLEAN DATA FOR FORECAST
# -------------------------------------------------------
output = {
    'monthly_2025': {int(row['Month']): {
        'recognized': float(row['Recognized']),
        'funding': float(row['Funding']),
        'count': int(row['Count'])
    } for _, row in monthly_2025.iterrows()},
    'monthly_2026_all': {int(row['Month']): {
        'recognized': float(row['Recognized']),
        'funding': float(row['Funding']),
        'count': int(row['Count'])
    } for _, row in monthly_2026_all.iterrows()},
    'monthly_2026_actual': {int(row['Month']): {
        'recognized': float(row['Recognized']),
        'count': int(row['Count'])
    } for _, row in monthly_2026_actual.iterrows()},
    'total_2025': float(total_2025)
}

with open('/home/ubuntu/monthly_actuals.json', 'w') as f:
    json.dump(output, f, indent=2)

print("\n\nSaved to monthly_actuals.json")
