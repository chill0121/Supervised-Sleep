# Supervised-Sleep

This project has evolved from an initial focus on statistical inference and machine learning exploration into a fully automated **end-to-end data pipeline**. The original analysis—covering EDA, feature engineering, statistical modeling, and machine learning—remains a valuable reference. However, the new implementation prioritizes **real-time data processing, structured storage, and actionable insights** using a streamlined pipeline.  

## **Project Overview**  

The pipeline is designed to fetch biometric and activity data from the Oura API, process and store it in a normalized relational database, serve it efficiently through a custom FastAPI backend, and visualize key insights in an interactive dashboard.  

### **Pipeline Flow**  

1. **Data Ingestion:**  
   - Scheduled API requests fetch data from the Oura API.  
   - Implements batching to handle API constraints while ensuring up-to-date data.  

2. **Data Processing & Storage:**  
   - **Data normalization**: Raw data is structured into relational tables to maintain integrity.  
   - **Handling incomplete data**: Partial records (e.g., current day’s data) are flagged as pending and updated upon finalization.  
   - **Foreign key resolution**: Ensures relationships (e.g., linking heartrate to sleep sessions) remain intact.  

3. **FastAPI Backend:**  
   - Exposes RESTful API endpoints to serve both raw and preprocessed data to the dashboard.  
   - Uses materialized views to precompute frequently queried datasets, reducing database load.  

4. **Dashboard Visualization:**  
   - Displays sleep trends, heartrate insights, stress levels, and summary statistics.  
   - Features a color-coded sleep calendar and dynamic filters for user-adjustable views.  
   - Future plans include machine learning-powered sleep recommendations based on biometric patterns.  

### **Next Steps (In Progress)**  
- Implement ML models to generate personalized sleep improvement suggestions.  
- Optimize query efficiency for large datasets (e.g., heartrate) using additional indexing strategies.  
- Expand API functionality to allow for real-time user interactions with the dashboard.  

This system provides a scalable, efficient, and interpretable framework for analyzing personal biometric data, making it an ideal foundation for future predictive analytics.

The repository’s file structure has been updated to reflect this transition, marking the deprecation of the original implementation, and can be now found in the `./sleep_analysis` folder.

## **Issues Encountered & Solutions**

### **1. Handling Incomplete & Redundant Data**
#### **Issue:**
- API fetches include a one-day overlap between consecutive pulls, ensuring consistency but introducing redundant and incomplete data.
- Some real-time metrics (e.g., `activity`, `workout`) remain incomplete until the end of the current day.

#### **Solution:**
- **API Level:**
  - The fetching function sets the last recorded end date as the new start date, minimizing redundant requests.
  - Introduced a **pending flag**:
    - Data for the current day is marked as `pending=True`.
    - On the next fetch, entries with `pending=True` are overwritten with the final complete data.

- **Database Level:**
  - The database temporarily stores incomplete data while tracking its pending status.
  - When a future API pull retrieves complete data, the database replaces pending entries.
  - Ensures the dashboard always displays the most recent available data while seamlessly updating incomplete entries.

### **2. API Data Fetching Constraints**
#### **Issue:**
- Oura API limits data fetches to 15-day intervals when including heartrate data.

#### **Solution:**
- Implemented a function to iteratively fetch historical data in **15-day increments**.
- Ensures a complete backfill while adhering to API constraints.

### **3. Data Retention & Conflict Handling**
#### **Issue:**
- Using `ON DELETE CASCADE` for all tables caused unnecessary deletions of linked data.

#### **Solution:**
- Applied `ON CONFLICT` resolution for `heartrate`, ensuring it persists while allowing `daily_sleep` and `daily_activity` to cascade.
- Preserves continuous datasets (e.g., heartrate) while maintaining structured daily records.

### **4. Handling Foreign Key Dependencies in Heartrate Table**
#### **Issue:**
- `daily_sleep_id` and `daily_activity_id` were `NULL` due to cascade effects when updating pending data.

#### **Solution:**
- Implemented `reassign_heartrate_foreign_keys()` to correctly link heartrate data after updates.
- Prevents data loss and maintains accurate associations.

### **5. Handling Missing API Response Fields**
#### **Issue:**
- Some API responses lacked expected keys, leading to `KeyError` during processing.

#### **Solution:**
- Modified `set_pending_flag()` to check for missing keys and log inconsistencies.
- Prevents crashes and facilitates debugging.

### **6. Optimizing Query Performance for Dashboard**
#### **Issue:**
- Frequently queried data (e.g., sleep calendar, heartrate trends) led to performance bottlenecks.

#### **Solution:**
- Implemented **materialized views** to precompute common queries.
- Reduces query load and improves dashboard responsiveness.

### **7. Structuring API for Dashboard & ML Model Integration**
#### **Issue:**
- Needed an efficient API to serve data to both the dashboard and future ML models.

#### **Solution:**
- Designed FastAPI endpoints for:
  - Default dashboard data.
  - User-adjustable queries.
  - ML model access.
- Ensures scalability and modularity.

### **8. Handling Large Heartrate Datasets**
#### **Issue:**
- Large heartrate datasets made real-time querying inefficient.

#### **Solution:**
- Preprocessed heartrate trends (e.g., last 3 months, min/max/avg over last 3 days) upon data insertion.
- Reduces computational overhead, improving dashboard performance.

---

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