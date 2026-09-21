# EDA findings (400k stratified sample; missingness from the full 7.7M rows)

- **Class balance:** Severity 1/2/3/4 = 0.87% / 79.67% / 16.81% / 2.65%. The sample matches the full data exactly.
- **Missingness (full data):** Precipitation 28.5%, Wind_Chill 25.9%, Wind_Speed 7.4%, other weather fields ~2%.
  End_Lat/End_Lng are 44% missing (and are post-hoc fields, so they are excluded anyway).
- **Outliers:** Temperature reaches 196 F, Wind_Speed 822 mph, Pressure 58 in and Visibility 100 mi. These are sensor or entry errors and are handled in preprocessing.
- **Severity labelling is NOT consistent across data sources or years (important):**

| year | Source1 share Sev3-4 | Source2 share Sev3-4 |
|------|------|------|
| 2016-2018 | 28-34% | 36-37% |
| 2019 | 21% | 30% |
| 2020 | 10% | 31% |
| 2021 | 2.5% | 34% |
| 2022-23 | 2.8% | 35% |

  Source1 has ~80k rows/year from 2021 on, and its high-severity rate collapses from ~33% to ~3%. Source2 stays flat at ~35%.
  Overall Sev3-4 share by year therefore falls from 36% (2018) to 3% (2023). This looks like a change in how the
  Severity label is assigned per provider, not a change in real-world risk.
  **Consequences:** (1) `Source` and year are excluded from the model features, since they are not driving conditions. (2) A time-based
  split trains and tests on very different base rates, so it is reported as a stress test, not as the headline result.
  (3) Any model can still pick up provider effects indirectly, for example through geography, and this cannot be fully removed.
- The dataset contains only accidents that happened, with no "no-accident" rows. The model therefore estimates
  P(high delay impact | an accident occurred under these conditions), NOT the probability that an accident occurs.
