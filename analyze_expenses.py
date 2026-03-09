import json
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Load all data chunks
all_rows = []

# Load first chunk (includes header)
with open('/home/ubuntu/sf_expense_data.json') as f:
    d = json.load(f)
rows = d.get('values', [])
headers = rows[0]
all_rows.extend(rows[1:])  # skip header

# Load remaining chunks
for i in range(2, 7):
    try:
        with open(f'/home/ubuntu/sf_expense_data{i}.json') as f:
            d = json.load(f)
        rows = d.get('values', [])
        if rows:
            all_rows.extend(rows)
    except FileNotFoundError:
        break

print(f"Total data rows: {len(all_rows)}")
print(f"Headers: {headers}")

# Create DataFrame - pad rows that are shorter than headers
padded_rows = []
for row in all_rows:
    if len(row) < len(headers):
        row = row + [''] * (len(headers) - len(row))
    padded_rows.append(row[:len(headers)])

df = pd.DataFrame(padded_rows, columns=headers)
print(f"\nDataFrame shape: {df.shape}")
print(f"\nColumn dtypes before conversion:")
print(df.dtypes)

# Parse key columns
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
    for fmt in ['%m/%d/%Y', '%Y-%m-%d', '%m/%d/%y', '%d/%m/%Y']:
        try:
            return pd.to_datetime(val, format=fmt)
        except:
            pass
    try:
        return pd.to_datetime(val)
    except:
        return pd.NaT

# Parse amounts
df['Recognized_Amount'] = df['Recognized Amount'].apply(parse_currency)
df['Funding_Amount'] = df['Funding: Funding Amount'].apply(parse_currency)
df['Payment_Amount'] = df['Milestone: Payment Amount'].apply(parse_currency)
df['Is_Actual'] = df['Actual?'].apply(lambda x: parse_currency(x))

# Parse dates
df['Spend_Date'] = df['Spend Recognition Date'].apply(parse_date)
df['Approval_Date'] = df['Milestone: Approval Date'].apply(parse_date)

# Filter rows with valid spend dates
df_dated = df[df['Spend_Date'].notna()].copy()
print(f"\nRows with valid Spend Recognition Date: {len(df_dated)}")

# Extract time dimensions
df_dated['Year'] = df_dated['Spend_Date'].dt.year
df_dated['Month'] = df_dated['Spend_Date'].dt.month
df_dated['Month_Name'] = df_dated['Spend_Date'].dt.strftime('%b')
df_dated['Quarter'] = df_dated['Spend_Date'].dt.quarter
df_dated['Quarter_Label'] = 'Q' + df_dated['Quarter'].astype(str)
df_dated['Year_Month'] = df_dated['Spend_Date'].dt.to_period('M')
df_dated['Year_Quarter'] = df_dated['Year'].astype(str) + '-' + df_dated['Quarter_Label']

print(f"\nDate range: {df_dated['Spend_Date'].min()} to {df_dated['Spend_Date'].max()}")
print(f"\nYears in data: {sorted(df_dated['Year'].unique())}")
print(f"\nPillars: {df_dated['Pillar'].unique()[:10]}")
print(f"\nAccounting Treatments: {df_dated['Accounting Treatment'].unique()}")
print(f"\nPipeline Statuses: {df_dated['Funding: Pipeline Status'].unique()}")

# --- MONTHLY BREAKDOWN ---
monthly = df_dated.groupby(['Year', 'Month', 'Month_Name']).agg(
    Total_Recognized=('Recognized_Amount', 'sum'),
    Total_Funding=('Funding_Amount', 'sum'),
    Count=('Recognized_Amount', 'count')
).reset_index()
monthly = monthly.sort_values(['Year', 'Month'])
monthly['Year_Month_Label'] = monthly['Month_Name'] + ' ' + monthly['Year'].astype(str)

# --- QUARTERLY BREAKDOWN ---
quarterly = df_dated.groupby(['Year', 'Quarter', 'Quarter_Label']).agg(
    Total_Recognized=('Recognized_Amount', 'sum'),
    Total_Funding=('Funding_Amount', 'sum'),
    Count=('Recognized_Amount', 'count')
).reset_index()
quarterly = quarterly.sort_values(['Year', 'Quarter'])
quarterly['Year_Quarter_Label'] = quarterly['Year'].astype(str) + ' ' + quarterly['Quarter_Label']

# --- BY PILLAR ---
pillar_monthly = df_dated.groupby(['Year', 'Month', 'Pillar']).agg(
    Total_Recognized=('Recognized_Amount', 'sum')
).reset_index()

pillar_quarterly = df_dated.groupby(['Year', 'Quarter', 'Quarter_Label', 'Pillar']).agg(
    Total_Recognized=('Recognized_Amount', 'sum')
).reset_index()

# --- BY ACCOUNTING TREATMENT ---
treatment_quarterly = df_dated.groupby(['Year', 'Quarter', 'Quarter_Label', 'Accounting Treatment']).agg(
    Total_Recognized=('Recognized_Amount', 'sum')
).reset_index()

# --- BY STATUS ---
status_summary = df_dated.groupby(['Funding: Pipeline Status']).agg(
    Total_Recognized=('Recognized_Amount', 'sum'),
    Total_Funding=('Funding_Amount', 'sum'),
    Count=('Recognized_Amount', 'count')
).reset_index().sort_values('Total_Recognized', ascending=False)

# --- TOP PILLARS ---
top_pillars = df_dated.groupby('Pillar').agg(
    Total_Recognized=('Recognized_Amount', 'sum')
).reset_index().sort_values('Total_Recognized', ascending=False).head(10)

# --- YEARLY SUMMARY ---
yearly = df_dated.groupby('Year').agg(
    Total_Recognized=('Recognized_Amount', 'sum'),
    Total_Funding=('Funding_Amount', 'sum'),
    Count=('Recognized_Amount', 'count')
).reset_index()

print("\n=== YEARLY SUMMARY ===")
print(yearly.to_string())

print("\n=== QUARTERLY BREAKDOWN ===")
print(quarterly.to_string())

print("\n=== MONTHLY BREAKDOWN (last 24 months) ===")
print(monthly.tail(24).to_string())

print("\n=== TOP PILLARS ===")
print(top_pillars.to_string())

print("\n=== STATUS SUMMARY ===")
print(status_summary.to_string())

# Save processed data for dashboard
output = {
    'monthly': monthly.to_dict(orient='records'),
    'quarterly': quarterly.to_dict(orient='records'),
    'yearly': yearly.to_dict(orient='records'),
    'pillar_monthly': pillar_monthly.to_dict(orient='records'),
    'pillar_quarterly': pillar_quarterly.to_dict(orient='records'),
    'treatment_quarterly': treatment_quarterly.to_dict(orient='records'),
    'status_summary': status_summary.to_dict(orient='records'),
    'top_pillars': top_pillars.to_dict(orient='records'),
    'date_range': {
        'min': str(df_dated['Spend_Date'].min()),
        'max': str(df_dated['Spend_Date'].max())
    },
    'total_rows': len(df_dated)
}

with open('/home/ubuntu/expense_analysis.json', 'w') as f:
    json.dump(output, f, default=str)

print("\n\nData saved to expense_analysis.json")
