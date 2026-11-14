# Findings and Premise Test - DMart Capstone Project

## 1. Store-wise Summary Table
| Store | Mean Daily Revenue (INR) | Mean Footfall | Mean Stockout Hours | Revenue per Footfall | Mean Achievement (%) | Poor Days |
|---|---|---|---|---|---|---|
| Ahmedabad | 782647.37 | 1922.59 | 3.19 | 407.08 | 92.08 | 1 |
| Bengaluru | 931065.68 | 2076.86 | 2.38 | 448.31 | 98.01 | 0 |
| Hyderabad | 893233.01 | 2209.51 | 3.85 | 404.27 | 94.02 | 0 |
| Mumbai | 1064371.6 | 2391.27 | 1.93 | 445.11 | 101.37 | 0 |
| Pune | 636358.55 | 1517.72 | 2.32 | 419.29 | 70.71 | 70 |
| All stores | 861535.24 | 2023.59 | 2.74 | 425.75 | 91.24 | 71 |

## 2. Premise Test: Does Pune have the most stockout hours?
Ranking of all five stores by mean stockout hours:
1. **Hyderabad:** 3.85 hours
2. **Ahmedabad:** 3.19 hours
3. **Bengaluru:** 2.38 hours
4. **Pune:** 2.32 hours
5. **Mumbai:** 1.93 hours

*All-store average stockout hours:* 2.74 hours.
**Conclusion:** Pune ranks 4th out of 5 stores in terms of mean stockout hours. Therefore, Kavita Rao's working premise—that Pune has the lowest revenue because of excessive stockouts—is **not supported** by the data.

## 3. Correlation Analysis
- **All rows (Revenue vs Stockout Hours):** -0.152
- **All rows (Revenue vs Footfall):** 0.918
- **Pune rows (Revenue vs Stockout Hours):** -0.254
- **Pune rows (Revenue vs Footfall):** 0.735
- **Raw deduplicated data (Revenue vs Footfall with anomalies):** 0.548

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
