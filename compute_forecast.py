import json
import numpy as np
from datetime import datetime

with open('/home/ubuntu/expense_analysis.json') as f:
    data = json.load(f)

# ---- FORECAST LOGIC ----
# Use 2022-2025 actuals to forecast 2026 (current year) and 2027+
# We have partial 2026 data (Q1 actual, Q2-Q4 forecast/committed)

yearly = data['yearly']
quarterly = data['quarterly']
monthly = data['monthly']

# Convert to dicts keyed by year
yearly_dict = {y['Year']: y for y in yearly}

# Historical actuals: 2022-2025 are the most reliable full years
hist_years = [2022, 2023, 2024, 2025]
hist_recognized = [yearly_dict[y]['Total_Recognized'] for y in hist_years]

# Growth rates
growth_rates = []
for i in range(1, len(hist_recognized)):
    if hist_recognized[i-1] > 0:
        growth_rates.append((hist_recognized[i] - hist_recognized[i-1]) / hist_recognized[i-1])

print("Historical growth rates:", [f"{r:.1%}" for r in growth_rates])
avg_growth = np.mean(growth_rates)
print(f"Average growth rate: {avg_growth:.1%}")

# For 2026 forecast: we have data in the sheet for 2026 (committed + forecast)
# The sheet already has 2026 data - use it as the forecast
# For 2027+, apply a moderated growth assumption

# Build quarterly forecast data
# Actual quarters: 2022-2025 full, 2026 Q1 (partial actuals)
# Forecast: 2026 Q2-Q4, 2027 full

# Quarterly data by year
quarterly_by_year = {}
for q in quarterly:
    yr = q['Year']
    if yr not in quarterly_by_year:
        quarterly_by_year[yr] = {}
    quarterly_by_year[yr][q['Quarter']] = q

# Monthly data by year-month
monthly_lookup = {}
for m in monthly:
    key = (m['Year'], m['Month'])
    monthly_lookup[key] = m

# Build complete monthly series for 2022-2026
months_order = []
for yr in range(2022, 2027):
    for mo in range(1, 13):
        key = (yr, mo)
        val = monthly_lookup.get(key, {'Total_Recognized': 0, 'Total_Funding': 0, 'Count': 0})
        months_order.append({
            'year': yr,
            'month': mo,
            'recognized': val['Total_Recognized'],
            'funding': val['Total_Funding'],
            'count': val['Count'],
            'label': f"{['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][mo-1]} {yr}"
        })

# Build quarterly series
quarters_order = []
for yr in range(2022, 2028):
    for q in range(1, 5):
        qdata = quarterly_by_year.get(yr, {}).get(q, {'Total_Recognized': 0, 'Total_Funding': 0, 'Count': 0})
        quarters_order.append({
            'year': yr,
            'quarter': q,
            'recognized': qdata['Total_Recognized'],
            'funding': qdata['Total_Funding'],
            'count': qdata['Count'],
            'label': f"{yr} Q{q}",
            'is_forecast': yr >= 2027 or (yr == 2026 and q >= 2)  # 2026 Q2+ and 2027 are forward-looking
        })

# Pillar breakdown by quarter
pillar_q = {}
for pq in data['pillar_quarterly']:
    yr = pq['Year']
    q = pq['Quarter']
    pillar = pq['Pillar']
    key = (yr, q)
    if key not in pillar_q:
        pillar_q[key] = {}
    pillar_q[key][pillar] = pq['Total_Recognized']

# Top pillars
top_pillars = [p['Pillar'] for p in data['top_pillars'][:8]]

# Build pillar quarterly series
pillar_quarterly_series = {}
for pillar in top_pillars:
    series = []
    for yr in range(2022, 2028):
        for q in range(1, 5):
            val = pillar_q.get((yr, q), {}).get(pillar, 0)
            series.append({
                'year': yr,
                'quarter': q,
                'label': f"{yr} Q{q}",
                'recognized': val
            })
    pillar_quarterly_series[pillar] = series

# Accounting treatment quarterly
treatment_q = {}
for tq in data['treatment_quarterly']:
    yr = tq['Year']
    q = tq['Quarter']
    treatment = tq['Accounting Treatment']
    key = (yr, q)
    if key not in treatment_q:
        treatment_q[key] = {}
    treatment_q[key][treatment] = tq['Total_Recognized']

treatments = list(set(tq['Accounting Treatment'] for tq in data['treatment_quarterly'] if tq['Accounting Treatment']))

treatment_quarterly_series = {}
for t in treatments:
    series = []
    for yr in range(2022, 2028):
        for q in range(1, 5):
            val = treatment_q.get((yr, q), {}).get(t, 0)
            series.append({
                'year': yr,
                'quarter': q,
                'label': f"{yr} Q{q}",
                'recognized': val
            })
    treatment_quarterly_series[t] = series

# YoY comparison
yoy = {}
for yr in [2023, 2024, 2025, 2026]:
    prev = yearly_dict.get(yr-1, {}).get('Total_Recognized', 0)
    curr = yearly_dict.get(yr, {}).get('Total_Recognized', 0)
    if prev > 0:
        yoy[yr] = (curr - prev) / prev
    else:
        yoy[yr] = 0

print("\nYoY growth:")
for yr, g in yoy.items():
    print(f"  {yr}: {g:.1%}")

# Forecast for 2027 using 2026 data with moderated growth
# 2026 total from sheet data
recognized_2026 = yearly_dict.get(2026, {}).get('Total_Recognized', 0)
recognized_2025 = yearly_dict.get(2025, {}).get('Total_Recognized', 0)

# Use the data already in the sheet for 2027 (it has committed/forecast entries)
recognized_2027_sheet = yearly_dict.get(2027, {}).get('Total_Recognized', 0)

print(f"\n2025 Recognized: ${recognized_2025:,.0f}")
print(f"2026 Recognized (sheet): ${recognized_2026:,.0f}")
print(f"2027 Recognized (sheet): ${recognized_2027_sheet:,.0f}")

# Build summary stats
summary_stats = {
    'total_records': data['total_rows'],
    'date_range': data['date_range'],
    'yearly': data['yearly'],
    'quarterly': quarters_order,
    'monthly': months_order,
    'top_pillars': data['top_pillars'],
    'status_summary': data['status_summary'],
    'pillar_quarterly': pillar_quarterly_series,
    'treatment_quarterly': treatment_quarterly_series,
    'yoy_growth': {str(k): v for k, v in yoy.items()},
    'treatments': treatments
}

with open('/home/ubuntu/expense_dashboard/dashboard_data.json', 'w') as f:
    json.dump(summary_stats, f, default=str)

print("\nDashboard data saved!")
