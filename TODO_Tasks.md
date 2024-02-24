##### TODO List

**TODO: General**
- [X] Collinearity/Multicollinearity between features checks in model selection.
- [X] Feature standardization/normalization.
- [X] Create Readme.
- [X] Create environment file for reproducibility.
- [X] Reroute filepath to align with github cloning.
- [X] Deal with NaNs using a generalized method.
- [X] Bin the Ys!
  - [X] Even-width bins.
  - [X] Quantile bin method.
  - [X] Visualize methods.
- [X] Balance train and test split classes. Note: Only works with more data, currently remove outliers (when class n < 2).
- [X] Implement regression friendly dataframe.
- [X] ROC Curve and/or F1.
- [ ] Previous Day's Sleep Score feature (assuming previous day sleep affects current day).
- [ ] oversampling/SMOTE.
- [X] Different models.
- [X] Reduce Features.
  - [X] Correlation matrix.
    - [X] Manual removal.
    - [ ] Automated solution.
  - [ ] Recursive solution: forward, backward, best subset.
  - [ ] sklearn.feature_selection >> RFE.
- [X] Define the problem.
  - [X] Choose logistic regression or regression and make a case for why.
- [ ] Ensemble solution?
- [X] Combine X and y DFs into one and rework train/test split.
- [ ] Address justification for EDA before train/test split.
- [ ] Prediction Intervals at each prediction ,using predict(SE = True), on plot.
- [ ] Linked Table of Contents
- [ ] Xlim the bin graph 0-100.
- [ ] Comparison of bins.
- [ ] Add regression line to sleep score vs types of sleep (EDA). Also makes points smaller.
- [ ] Declare alpha to hypothesis testing.

**TODO: oura_sleep_2024-01.csv**
- [x] Nap boolean encoding per day.
  - [X] `list(where ['type'] != long_sleep && between 9 AM - 6 PM)`
    - [ ] Does the nap affect day of or next day?
  - [X] sum(types of sleep duration).
- [ ] restless_periods vs sum(movement_30_sec) ??
- [X] Only one day per entry.
  - [X] Sum each day sleep durations, restless_periods, awake_time, time_in_bed, total_sleep_duration.
  - [X] `awake_time = time_in_bed - total_sleep_duration` | Yes
- [X] Save only the `['type'] == long_sleep, average_breath, average_heart_rate, average_hrv, latency, 
       lowest_heart_rate, betime_start_delta`.
- [X] Remove: `efficiency, period, score, segment_state, sleep_midpoint, sleep_phase_5_min, movement_30_sec, timezone, 
       betime_end_delta, midpoint_at_delta, heart_rate_5_min, hrv_5_min`.

**TODO: oura_daily-activity_2024-01.csv**
- [X] Remove: `average_met_minutes, equivalent_walking_distance, high_activity_met_minutes, inactivity_alerts, 
       low_activity_met_minutes, medium_activity_met_minutes, sedentary_met_minutes, target_calories, target_meters, score,
       class_5_min, met_1_min, ring_met_1_min`.
- [ ] Workout today? daily boolean (Maybe unnecessary with other metrics compare models w/ and w/o).
- [X] Assign all activity to previous day to align with target variable.

**TODO: oura_daily-readiness_2024-01.csv**
- [X] Remove: `score, temperature_trend_deviation`.