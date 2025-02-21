# Supervised-Sleep

This project is evolving from its original focus on statistical inference and machine learning exploration into a full end-to-end data pipeline. While the original analysis—covering EDA, feature engineering, statistical modeling, and machine learning—will remain as a valuable reference, the revamped version will emphasize automation, real-time data processing, and actionable insights from biometric data.

The new pipeline will include:

1. Scheduled API requests for data collection
2. A data cleaning module
3. Storage in an SQL database
4. Machine learning modules for analysis
5. A web-based dashboard for visualization

The repository’s file structure will be updated to reflect this transition, marking the deprecation of the original implementation, and can be now found in the `./sleep_analysis` folder.

## Issues encountered during the project and their solutions:

1. Data redundancy and today's data is always incomplete.
  - The data fetching function looks to find the most recent API pull and uses the last end date as the new start date. This limits the redundancy to the just the last day of data that was pulled. While, this is beneficial because it limits the redundancy it also creates an issue where every pull will always include a partial day's amount of data. Only pulling data up until yesterday is not an options as one of the goals of the dashboard is to show current metrics of sleep which are included in today's data. Several solutions will be implemented to mitigate this issue and achieve this outcome.
    - API:
      - To mitigate major redundancy in the data and API requests, the data fetching function looks to find the most recent API pull and uses the last end date as the new start date. This limits the redundancy to the just the last day of data that was pulled. This is actually beneficial because every pull will always include a partial day's amount of data.
      - Some of the partial data pulled is useful, such as: `daily_sleep`, `daily_activity`, etc -- as they contain the calculate scores of the previous day. However, data like `activity` and `workout` pertain to the current day and will be incomplete until the day is over, thus needing to be dealt with during a future data fetch. This will be accomplished using a `pending` flag, if the date of the data that is about to be stored matches today's date, a pending flag will be set to `True`. During the next future data fetch, the start date (which will be the previous end date) will overwrite any data with a True pending flag.
    - Database:
      - Since we still want the ability for the dashboard to display impartial data, the database will need to keep track of the impartial data issue as well and overwrite the impartial day's data when a future API pull completes it.

*This project is licensed under the terms of the MIT License, but is intended for private use only.*

*If you fork or use any part of this project please attribute Cody Hill as the creator of this work.*

---

## Sleep Analysis Description:

Sleep quality predictions using supervised machine learning.

This project is intended as a demonstration and exploring in training machine learning predictive models on Oura Ring exported user data. The ground truth target variable is the sleep score assigned to each day from the exported data. Along with the goal of creating a well-fit model for this problem, both regression and classification models will be used in this project, exploring the efficacy of turning the discrete sleep scores into ordinal categorical variables.

Since the data collection period is currently limited, this project has been made with the goal of handling continued data uploads (all data cleaning/analysis will be generalized for continuous new data).


---

### Environment Information / Dependencies:

Python version: 3.11.7 (main, Dec  4 2023, 18:10:11) [Clang 15.0.0 (clang-1500.1.0.2.5)]\
module 'numpy'  using version: 1.26.3\
module 'pandas'  using version: 2.1.4\
module 'sklearn'  using version: 1.3.2\
module 'scipy'  using version: 1.11.4\
module 'statsmodels.api'  using version: 0.14.1\
module 'matplotlib'  using version: 3.8.2\
module 'seaborn'  using version: 0.13.2

### Parameters you might be interested in changing:

- Train Test Split Section 7:
  - `rand_state` = 87654321
  - `test_ratio` = 0.2
  - `bin_type` = 'score_bin_custom'

### Data Source Information

All data has been exported from my personal Oura Ring containing raw biometric data and Oura calculated data since I began wearing the device.

The Oura Ring tracks and records over 20 biometric signals from the sensors on the inside of the ring throughout the day and during sleep. Along with the raw biometric data, Oura's software engineers new metrics to assist in calculating a daily score assigned to categories such as sleep, recovery, readiness, activity, etc.. In total 89 features can be extracted from a user's account giving historical data since the beginning of the user's wear time. Most of these features are daily cumulative sums of metrics or other measures that typically have 1 entry per day, but the sleep data has entries for every time a user is sleeping, potentially allowing for multiple entries per day.

**Notable Data Information:**
- Data collection starting 2/3/2023 to 2/6/2024 (last upload) ~~1/18/2024~~
- Oura Ring Gen. 3 | Firmware: 2.9.32
- 89 Total Features
- 369 rows of biometric data, which equates to 369 days of data.
- 730 rows of sleep data, which equates to that number of sleep events recorded.

- **Feature Information** *(more info can be found at https://cloud.ouraring.com/edu/sleep_score)*:
  - **Sleep Score**: (`score`) Ranging from 0-100, the sleep score is an overall measure of how well you slept.
  - **Awake Time**: (`awake_time`) Awake time is the time spent awake in bed before and after falling asleep.
  - **Bedtime**: (`bedtime_start_delta`) Bedtime is an estimate of the time you went to bed with the intention to sleep. Delta measures the difference of your bedtime compared to your regular bedtime (calculates continuously).
  - **Deep Sleep Time**: (`deep_sleep_duration`) Deep sleep is the most restorative and rejuvenating sleep stage, enabling muscle growth and repair. The amount of deep sleep can vary significantly between nights and individuals. It can make up anywhere between 0-35% of your total sleep time.
  - **Light Sleep Time**: (`light_sleep_duration`) Light sleep makes up about 50% of total sleep time for adults, and typically begins a sleep cycle.
  - **REM Sleep Time**: (`rem_sleep_duration`) REM (rapid eye movement) sleep is the final sleep stage in a typical sleep cycle. It’s associated with dreaming, memory consolidation, learning and creativity.
  - **Total Sleep Time**: (`total_sleep_duration`) Total sleep time refers to the total amount of time you spend in light, REM, and deep sleep.
  - **Respiratory Rate**: (`average_breath`) Oura tracks the number of breaths you take per minute while you sleep, and shows your nocturnal average respiratory rate.
  - **Sleep Latency**: (`latency`) Sleep latency is the time it takes for you to fall asleep.
  - **Average HRV**: (`average_hrv`) When a person is relaxed, a healthy heart’s beating rate shows variation in the time interval between heartbeats.
  - **Body Temperature**: (`temperature_deviation`) Oura measures your body temperature while you sleep. It sets the baseline for your normal temperature during the first couple of weeks, and adjusts it if needed as more data is collected. Variations are shown in relation to your baseline, represented by 0.0.
  - **Activity Burn**: (`active_calories`) Activity burn shows the kilocalories you've burned by daily movement and exercise.
  - **Low Activity**: (`low_activity_time`) Low activity includes activities such as casual walking and light housework both indoors and outdoors.
  - **Medium Activity**: (`medium_activity_time`) Medium activity includes dynamic activities with an intensity level equivalent to brisk walking.
  - **High Activity**: (`high_activity_time`) High activity includes vigorous activities with an intensity level higher or equivalent to jogging.
  - **Inactive Time**: (`sedentary_time`) Inactive time includes sitting, standing or otherwise being passive.