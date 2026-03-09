import json
import numpy as np

# -------------------------------------------------------
# RAW DATA — from sheet extraction
# -------------------------------------------------------

MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

# 2025 full-year monthly actuals (from sheet)
actuals_2025 = {
    1:  19_101_685,
    2:  29_367_505,
    3:  48_069_873,
    4:  30_504_540,
    5:  35_545_623,
    6:  36_678_344,
    7:  44_323_900,
    8:  49_943_836,
    9:  79_512_767,
    10: 84_793_236,
    11: 60_317_630,
    12: 136_664_314,
}
total_2025 = sum(actuals_2025.values())  # $654,823,253

# 2026 Jan & Feb — full recognized (Option 2: all records)
actuals_2026_jan = 16_617_880
actuals_2026_feb = 21_970_774

# -------------------------------------------------------
# STEP 1: 2025 SEASONAL INDEX
# Method: each month's share of the full 2025 annual total
# -------------------------------------------------------
seasonal_index_2025 = {m: actuals_2025[m] / total_2025 for m in range(1, 13)}

print("=== 2025 Seasonal Index (% of annual total) ===")
for m in range(1, 13):
    print(f"  {MONTHS[m-1]:>3}: {seasonal_index_2025[m]*100:6.2f}%  (${actuals_2025[m]:>14,.0f})")
print(f"  Total index: {sum(seasonal_index_2025.values())*100:.1f}%")

# -------------------------------------------------------
# STEP 2: DERIVE THE IMPLIED 2026 ANNUAL RUN-RATE
# from Jan & Feb actuals vs their 2025 seasonal weights
#
# Logic: if Jan+Feb 2026 = $38.6M and they represent
# (Jan_idx + Feb_idx) = X% of the year in 2025 pattern,
# then implied full-year = $38.6M / X%
# -------------------------------------------------------
jan_feb_2025_share = seasonal_index_2025[1] + seasonal_index_2025[2]
jan_feb_2026_actual = actuals_2026_jan + actuals_2026_feb
implied_annual_2026 = jan_feb_2026_actual / jan_feb_2025_share

print(f"\n=== Implied Annual 2026 Run-Rate ===")
print(f"  Jan+Feb 2026 actuals:       ${jan_feb_2026_actual:>14,.0f}")
print(f"  Jan+Feb 2025 share of year: {jan_feb_2025_share*100:.2f}%")
print(f"  Implied 2026 annual total:  ${implied_annual_2026:>14,.0f}")
print(f"  vs 2025 actual:             ${total_2025:>14,.0f}")
print(f"  Implied YoY change:         {(implied_annual_2026/total_2025 - 1)*100:+.1f}%")

# -------------------------------------------------------
# STEP 3: FORECAST Mar–Dec 2026
# Apply 2025 seasonal index to implied 2026 annual total
# -------------------------------------------------------
forecast_2026 = {}
for m in range(1, 13):
    if m == 1:
        forecast_2026[m] = actuals_2026_jan   # actual
    elif m == 2:
        forecast_2026[m] = actuals_2026_feb   # actual
    else:
        forecast_2026[m] = seasonal_index_2025[m] * implied_annual_2026  # forecast

total_2026_forecast = sum(forecast_2026.values())

# -------------------------------------------------------
# STEP 4: QUARTERLY ROLLUP
# -------------------------------------------------------
def quarterly(monthly_dict):
    return {
        'Q1': sum(monthly_dict[m] for m in [1,2,3]),
        'Q2': sum(monthly_dict[m] for m in [4,5,6]),
        'Q3': sum(monthly_dict[m] for m in [7,8,9]),
        'Q4': sum(monthly_dict[m] for m in [10,11,12]),
    }

q_2025 = quarterly(actuals_2025)
q_2026 = quarterly(forecast_2026)

# -------------------------------------------------------
# PRINT FULL FORECAST TABLE
# -------------------------------------------------------
print(f"\n{'='*80}")
print(f"{'2026 FORECAST — FULL YEAR VIEW':^80}")
print(f"{'='*80}")
print(f"\n{'Month':<12} {'2025 Actual':>15} {'2025 Share':>11} {'2026 Actual/Fcst':>18} {'YoY Δ':>10} {'Type':>12}")
print("-"*80)

for m in range(1, 13):
    v25 = actuals_2025[m]
    v26 = forecast_2026[m]
    share = seasonal_index_2025[m] * 100
    yoy = (v26 / v25 - 1) * 100
    typ = "ACTUAL" if m <= 2 else "FORECAST"
    marker = "◆" if m <= 2 else "◇"
    print(f"{marker} {MONTHS[m-1]+' 2026':<10} ${v25:>14,.0f}  {share:>9.2f}%  ${v26:>16,.0f}  {yoy:>+9.1f}%  {typ:>12}")

print("-"*80)
print(f"  {'FULL YEAR':<10} ${total_2025:>14,.0f}  {'100.00%':>10}  ${total_2026_forecast:>16,.0f}  {(total_2026_forecast/total_2025-1)*100:>+9.1f}%")

print(f"\n{'='*80}")
print(f"{'QUARTERLY SUMMARY':^80}")
print(f"{'='*80}")
print(f"\n{'Quarter':<10} {'2025 Actual':>15} {'2026 Forecast':>16} {'YoY Δ':>10} {'2026 Notes':>20}")
print("-"*80)
q_notes = {
    'Q1': 'Jan+Feb actual, Mar fcst',
    'Q2': 'Apr–Jun forecast',
    'Q3': 'Jul–Sep forecast',
    'Q4': 'Oct–Dec forecast',
}
for q in ['Q1','Q2','Q3','Q4']:
    v25 = q_2025[q]
    v26 = q_2026[q]
    yoy = (v26 / v25 - 1) * 100
    print(f"  {q:<8} ${v25:>14,.0f}  ${v26:>14,.0f}  {yoy:>+9.1f}%  {q_notes[q]:>20}")
print("-"*80)
print(f"  {'FY2026':<8} ${total_2025:>14,.0f}  ${total_2026_forecast:>14,.0f}  {(total_2026_forecast/total_2025-1)*100:>+9.1f}%")

# -------------------------------------------------------
# ALSO SHOW: 2026 Sheet Data vs Trend Forecast comparison
# -------------------------------------------------------
sheet_2026 = {
    1: 16_617_880, 2: 21_970_774, 3: 47_292_713,
    4: 50_736_685, 5: 21_438_943, 6: 45_517_506,
    7: 17_520_772, 8: 22_925_373, 9: 19_290_780,
    10: 34_263_581, 11: 87_083_715, 12: 62_677_728,
}
total_sheet_2026 = sum(sheet_2026.values())

print(f"\n{'='*80}")
print(f"{'COMPARISON: TREND FORECAST vs SHEET PIPELINE DATA':^80}")
print(f"{'='*80}")
print(f"\n{'Month':<12} {'Trend Forecast':>16} {'Sheet Pipeline':>16} {'Difference':>14}")
print("-"*80)
for m in range(1, 13):
    tf = forecast_2026[m]
    sp = sheet_2026[m]
    diff = tf - sp
    print(f"  {MONTHS[m-1]+' 2026':<10} ${tf:>14,.0f}  ${sp:>14,.0f}  ${diff:>+13,.0f}")
print("-"*80)
print(f"  {'TOTAL':<10} ${total_2026_forecast:>14,.0f}  ${total_sheet_2026:>14,.0f}  ${total_2026_forecast-total_sheet_2026:>+13,.0f}")

# -------------------------------------------------------
# SAVE OUTPUT
# -------------------------------------------------------
output = {
    'actuals_2025': actuals_2025,
    'total_2025': total_2025,
    'seasonal_index_2025': seasonal_index_2025,
    'jan_2026_actual': actuals_2026_jan,
    'feb_2026_actual': actuals_2026_feb,
    'implied_annual_2026': implied_annual_2026,
    'forecast_2026': forecast_2026,
    'total_2026_forecast': total_2026_forecast,
    'sheet_2026': sheet_2026,
    'total_sheet_2026': total_sheet_2026,
    'quarterly_2025': q_2025,
    'quarterly_2026_forecast': q_2026,
}

with open('/home/ubuntu/forecast_2026_output.json', 'w') as f:
    json.dump(output, f, indent=2)

print("\n\nSaved to forecast_2026_output.json")
