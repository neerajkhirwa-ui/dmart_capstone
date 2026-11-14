"""Data cleaning script for DMart Capstone Project.
Reads data/store_daily.csv, writes data/store_daily_clean.csv and analysis/cleaning_log.csv.
"""

import os
import numpy as np
import pandas as pd

# 1. डेटा लोड करें
df = pd.read_csv("data/store_daily.csv")

logs = []

# 2. एक्जेक्ट डुप्लीकेट हटाएं (पहली वाली रखें)
initial_count = len(df)
df = df.drop_duplicates(keep="first")

# 3. नेगेटिव फुटफाल को missing (NaN) करें
negative_mask = df["footfall"] < 0
if negative_mask.any():
  for idx, row in df[negative_mask].iterrows():
    logs.append({
        "store": row["store"],
        "date": row["date"],
        "old_footfall": row["footfall"],
        "new_footfall": "",
        "rule": "negative_to_missing",
    })
  df.loc[negative_mask, "footfall"] = np.nan

# 4. स्टोर-वाइज IQR बाउंड्स कैलकुलेट करें और एक्सट्रीम वैल्यूज़ को कैप (cap) करें
stores = df["store"].dropna().unique()
store_bounds = {}

for store in stores:
  subset = df[df["store"] == store]["footfall"].dropna()
  q1 = subset.quantile(0.25, interpolation="linear")
  q3 = subset.quantile(0.75, interpolation="linear")
  iqr = q3 - q1
  lower = q1 - 1.5 * iqr
  upper = q3 + 1.5 * iqr
  store_bounds[store] = (lower, upper)

  # अपर बाउंड से ज्यादा वैल्यूज़ को कैप करें
  upper_mask = (df["store"] == store) & (df["footfall"] > upper)
  if upper_mask.any():
    for idx, row in df[upper_mask].iterrows():
      old_val = row["footfall"]
      capped_val = round(upper, 2)
      df.loc[idx, "footfall"] = capped_val
      logs.append({
          "store": store,
          "date": row["date"],
          "old_footfall": old_val,
          "new_footfall": f"{capped_val:.2f}",
          "rule": "iqr_cap",
      })

# 5. बचे हुए मिसिंग डेटा को स्टोर के मीडियन (median) से भरें
for store in stores:
  store_median = df[df["store"] == store]["footfall"].median()
  missing_mask = (df["store"] == store) & (df["footfall"].isna())
  if missing_mask.any():
    for idx, row in df[missing_mask].iterrows():
      df.loc[idx, "footfall"] = store_median
      logs.append({
          "store": store,
          "date": row["date"],
          "old_footfall": "",
          "new_footfall": f"{store_median:.1f}",
          "rule": "median_impute",
      })

# फुटफाल को integer में बदलें जहाँ जरूरत हो
df["footfall"] = df["footfall"].round().astype(int)

# 6. नए फीचर कॉलम्स जोड़ें
dt_series = pd.to_datetime(df["date"])

df["revenue_per_footfall"] = (df["revenue_inr"] / df["footfall"]).round(2)
df["marketing_efficiency"] = (
    df["revenue_inr"] / df["marketing_spend_inr"]
).round(2)
df["achievement_pct"] = (
    (df["revenue_inr"] / df["daily_target_inr"]) * 100
).round(2)
df["shortfall_inr"] = (df["daily_target_inr"] - df["revenue_inr"]).round(2)

# Weekend flag (Saturday=5, Sunday=6)
df["weekend_flag"] = dt_series.dt.day_of_week.apply(
    lambda x: "Yes" if x >= 5 else "No"
)


# Performance band
def get_band(ach):
  if ach >= 100:
    return "Excellent"
  elif ach >= 75:
    return "Good"
  else:
    return "Poor"


df["performance_band"] = df["achievement_pct"].apply(get_band)

# 7. क्लीन फाइल और लॉग सेव करें
os.makedirs("data", exist_ok=True)
os.makedirs("analysis", exist_ok=True)

df.to_csv("data/store_daily_clean.csv", index=False)

log_df = pd.DataFrame(logs)
log_df.to_csv("analysis/cleaning_log.csv", index=False)

print("Data cleaning completed successfully! Clean rows:", len(df))