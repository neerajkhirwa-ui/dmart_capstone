import pandas as pd
import numpy as np

# store_daily.csv को लोड करें
df = pd.read_csv("data/store_daily.csv")

# 1. डुप्लीकेट रो हटाएं
df_dedup = df.drop_duplicates(keep="first")

# 2. नेगेटिव फुटफाल को NaN (missing) करें
df_dedup.loc[df_dedup["footfall"] < 0, "footfall"] = np.nan

print("--- Per-Store Footfall Bounds (Q1, Q3, IQR) ---")
stores = df_dedup["store"].dropna().unique()

for store in stores:
    subset = df_dedup[df_dedup["store"] == store]["footfall"].dropna()
    q1 = subset.quantile(0.25, interpolation="linear")
    q3 = subset.quantile(0.75, interpolation="linear")
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    print(f"Store: {store} | Q1: {q1:.2f} | Q3: {q3:.2f} | Lower: {lower_bound:.2f} | Upper: {upper_bound:.2f}")