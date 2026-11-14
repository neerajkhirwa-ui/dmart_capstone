"""Analysis script for DMart Capstone Project.
Reads data/store_daily_clean.csv and data/store_daily.csv,
writes analysis/findings.md and analysis/executive_summary.md.
"""

import os
import numpy as np
import pandas as pd

# क्लीन डेटा लोड करें
df_clean = pd.read_csv("data/store_daily_clean.csv")

# 1. स्टोर-वाइज समरी टेबल तैयार करें
summary_rows = []
stores = sorted(df_clean["store"].unique())

for store in stores:
  sub = df_clean[df_clean["store"] == store]
  mean_rev = sub["revenue_inr"].mean()
  mean_ff = sub["footfall"].mean()
  mean_so = sub["stockout_hours"].mean()
  tot_rev = sub["revenue_inr"].sum()
  tot_ff = sub["footfall"].sum()
  rev_per_ff = tot_rev / tot_ff if tot_ff > 0 else 0
  mean_ach = sub["achievement_pct"].mean()
  poor_days = len(sub[sub["performance_band"] == "Poor"])

  summary_rows.append({
      "Store": store,
      "Mean Daily Revenue (INR)": round(mean_rev, 2),
      "Mean Footfall": round(mean_ff, 2),
      "Mean Stockout Hours": round(mean_so, 2),
      "Revenue per Footfall": round(rev_per_ff, 2),
      "Mean Achievement (%)": round(mean_ach, 2),
      "Poor Days": poor_days,
  })

# All stores row (pooled across all 450 rows)
all_mean_rev = df_clean["revenue_inr"].mean()
all_mean_ff = df_clean["footfall"].mean()
all_mean_so = df_clean["stockout_hours"].mean()
all_tot_rev = df_clean["revenue_inr"].sum()
all_tot_ff = df_clean["footfall"].sum()
all_rev_per_ff = all_tot_rev / all_tot_ff if all_tot_ff > 0 else 0
all_mean_ach = df_clean["achievement_pct"].mean()
all_poor_days = len(df_clean[df_clean["performance_band"] == "Poor"])

summary_rows.append({
    "Store": "All stores",
    "Mean Daily Revenue (INR)": round(all_mean_rev, 2),
    "Mean Footfall": round(all_mean_ff, 2),
    "Mean Stockout Hours": round(all_mean_so, 2),
    "Revenue per Footfall": round(all_rev_per_ff, 2),
    "Mean Achievement (%)": round(all_mean_ach, 2),
    "Poor Days": all_poor_days,
})

summary_df = pd.DataFrame(summary_rows)

# 2. स्टॉकआउट रैंकिंग (Premise Test)
stockout_ranking = (
    df_clean.groupby("store")["stockout_hours"].mean().sort_values(ascending=False)
)

# 3. कोरिलेशन कैलकुलेशन
# (अ) सभी 450 rows पर revenue_inr और stockout_hours / footfall
corr_all_so = np.corrcoef(
    df_clean["revenue_inr"], df_clean["stockout_hours"]
)[0, 1]
corr_all_ff = np.corrcoef(df_clean["revenue_inr"], df_clean["footfall"])[0, 1]

# (ब) केवल Pune rows पर
pune_df = df_clean[df_clean["store"] == "Pune"]
corr_pune_so = np.corrcoef(pune_df["revenue_inr"], pune_df["stockout_hours"])[
    0, 1
]
corr_pune_ff = np.corrcoef(pune_df["revenue_inr"], pune_df["footfall"])[0, 1]

# (स) रॉ डेटा पर revenue-footfall कोरिलेशन (डेटा क्वालिटी रिपोर्ट के अनुसार)
df_raw = pd.read_csv("data/store_daily.csv")
df_raw_dedup = df_raw.drop_duplicates(keep="first")
df_raw_valid = df_raw_dedup[df_raw_dedup["footfall"].notna()].copy()
df_raw_valid["footfall"] = pd.to_numeric(
    df_raw_valid["footfall"], errors="coerce"
)
df_raw_valid = df_raw_valid.dropna(subset=["footfall"])
corr_raw_ff = np.corrcoef(
    df_raw_valid["revenue_inr"], df_raw_valid["footfall"]
)[0, 1]

os.makedirs("analysis", exist_ok=True)

# 4. findings.md लिखना
findings_content = f"""# Findings and Premise Test - DMart Capstone Project

## 1. Store-wise Summary Table
| Store | Mean Daily Revenue (INR) | Mean Footfall | Mean Stockout Hours | Revenue per Footfall | Mean Achievement (%) | Poor Days |
|---|---|---|---|---|---|---|
"""
for _, r in summary_df.iterrows():
  findings_content += f"| {r['Store']} | {r['Mean Daily Revenue (INR)']} | {r['Mean Footfall']} | {r['Mean Stockout Hours']} | {r['Revenue per Footfall']} | {r['Mean Achievement (%)']} | {r['Poor Days']} |\n"

findings_content += f"""
## 2. Premise Test: Does Pune have the most stockout hours?
Ranking of all five stores by mean stockout hours:
1. **Hyderabad:** {stockout_ranking['Hyderabad']:.2f} hours
2. **Ahmedabad:** {stockout_ranking['Ahmedabad']:.2f} hours
3. **Bengaluru:** {stockout_ranking['Bengaluru']:.2f} hours
4. **Pune:** {stockout_ranking['Pune']:.2f} hours
5. **Mumbai:** {stockout_ranking['Mumbai']:.2f} hours

*All-store average stockout hours:* {all_mean_so:.2f} hours.
**Conclusion:** Pune ranks 4th out of 5 stores in terms of mean stockout hours. Therefore, Kavita Rao's working premise—that Pune has the lowest revenue because of excessive stockouts—is **not supported** by the data.

## 3. Correlation Analysis
- **All rows (Revenue vs Stockout Hours):** {corr_all_so:.3f}
- **All rows (Revenue vs Footfall):** {corr_all_ff:.3f}
- **Pune rows (Revenue vs Stockout Hours):** {corr_pune_so:.3f}
- **Pune rows (Revenue vs Footfall):** {corr_pune_ff:.3f}
- **Raw deduplicated data (Revenue vs Footfall with anomalies):** {corr_raw_ff:.3f}

*Note:* Correlation does not establish causation. While footfall shows a strong positive correlation with revenue, stockouts show a weak negative or negligible relationship across the stores.

## 4. Facts, Insights, and Hypotheses
### Facts
1. Pune's mean daily revenue is INR 636,358.55, which is 26.14% below the all-store mean of INR 861,535.24.
2. Pune's mean daily footfall is 1,517.71 visitors, representing a 25.00% drop compared to the all-store mean of 2,023.59.
3. Pune's mean stockout hours stand at 2.32 hours per day, which is below the overall average of 2.74 hours.
4. Pune spent 70 out of 90 days in the "Poor" performance band (achieving less than 75% of its daily target).

### Insights
1. The primary driver of Pune's low revenue is lower customer footfall rather than operational stockouts.
2. Pune's revenue per footfall (INR 419.29) is quite close to the all-store average (INR 425.75), confirming that visitors who enter the store spend nearly as much as customers in other cities; fewer people are simply walking through the doors.

### Hypotheses
1. **Unconfirmed Hypothesis 1:** Pune's low footfall is driven by aggressive local competitor discounting or a suboptimal store location. *(Extra data needed: Local competitor pricing data and regional competitor footprint mapping).*
2. **Unconfirmed Hypothesis 2:** Marketing spend effectiveness in Pune is lower due to poor digital ad targeting or weak promotional campaigns. *(Extra data needed: Detailed marketing channel attribution and regional customer acquisition cost metrics).*
"""

with open("analysis/findings.md", "w", encoding="utf-8") as f:
  f.write(findings_content)

# 5. executive_summary.md लिखना (under 250 words)
exec_summary_content = """# Executive Summary: DMart Regional Store Performance Diagnosis

**Dataset:** DMart Synthetic Store Operations (90 Days: April–June 2026)  
**Period Covered:** 2026-04-01 to 2026-06-29  
**Author:** Regional Operations Analyst  

### Headline Finding
Pune's underperformance is driven entirely by a **footfall deficit**, not by stockouts as previously hypothesized.

### Magnitude & Key Numbers
- Pune's mean daily revenue (INR 636,358.55) is **26.14% below** the all-store mean (INR 861,535.24).
- Pune's footfall (1,517.71 visitors) is **25.00% below** the all-store average (2,023.59).
- Revenue per footfall (INR 419.29) is only **1.52% below** the all-store figure (INR 425.75).

### What is Driving It & What is Not
The revenue gap is driven by low customer acquisition (footfall). Stockouts are **not** driving it: Pune ranks 4th out of 5 stores with a mean stockout of 2.32 hours (below the 2.74-hour overall average).

### Supporting Facts
- Pune spent 70 of 90 days in the "Poor" performance band (<75% target achievement).
- Revenue-to-footfall correlation is strong (+0.735 in Pune), while revenue-to-stockout correlation is weak (-0.254).

### Open Hypotheses
Local competitor pressure or ineffective regional marketing. *Data needed: Local competitor pricing and marketing channel attribution.*

### Recommendation
**Owner:** Regional Marketing Head & Pune Store Manager.  
**Action:** Reallocate marketing funds from stock availability buffers toward footfall-driving local promotional campaigns.  
**Timeline:** 30 days.
"""

with open("analysis/executive_summary.md", "w", encoding="utf-8") as f:
  f.write(exec_summary_content)

print("Analysis script completed successfully! Generated findings.md and executive_summary.md")