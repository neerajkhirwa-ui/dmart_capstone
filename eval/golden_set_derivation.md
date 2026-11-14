# Golden Set Derivation - DMart Capstone Project

This document outlines the derivations and calculations for custom test cases added to `eval/golden_set.csv`.

## Custom Test Cases Derivation

### 1. Case R01 (Full Period Store Comparison - Lowest Average Revenue)
- **Question:** Which store had the lowest average revenue between 2026-04-01 and 2026-06-29?
- **Derivation / Pandas Expression:**
  ```python
  import pandas as pd
  df = pd.read_csv("data/store_daily_clean.csv")
  means = df.groupby("store")["revenue_inr"].mean().sort_values(ascending=True)
  print(means)
  Calculated Results (Rounded Half-Up to 2 Decimals):

Pune: INR 636358.55

Ahmedabad: INR 782647.37

Hyderabad: INR 893233.01

Bengaluru: INR 931065.68

Mumbai: INR 1064371.60

Expected Substrings: Pune INR 636358.55, Ahmedabad INR 782647.37, Hyderabad INR 893233.01, Bengaluru INR 931065.68, Mumbai INR 1064371.60

2. Custom Case E01 (Synonym Verification)
Question: What was Pune's sales on 15 May 2026?

Derivation: Synonyms mapping sales to revenue_inr. Exact record for Pune on 2026-05-15 from store_daily_clean.csv.

Value: INR 623845.00

3. Custom Case E02 (Typo Verification)
Question: What was Punee's revenue on 15 May 2026?

Derivation: Fuzzy matching Punee against store list (Pune, score > 0.7).

Value: Pune, INR 623845.00

4. Custom Case E10 (Inventory Threshold Verification)
Question: Which stores are below the reorder threshold for Toor Dal 1kg?

Derivation / Pandas Expression:
df_inv = pd.read_csv("data/inventory.csv")
sub = df_inv[(df_inv["product"] == "Toor Dal 1kg") & (df_inv["stock_units"] < df_inv["reorder_threshold"])]
print(sub[["store", "stock_units", "reorder_threshold"]])
Value: Stores meeting the stock condition for Toor Dal 1kg with respective units and thresholds.