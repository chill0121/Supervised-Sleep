## **Database Schema**

The structure of the Oura API data naturally guided the design of this relational database. The majority of the nested keys of the JSON necessitated creating child tables (e.g., `sleep_contributors`), reducing redundancy and improving query performance.

### **Key Design Decisions**
1. **Separation of Readiness Data**
    - Readiness is a derived metric that depends on both sleep and activity from the previous day.
    - Instead of using foreign keys, which would introduce unnecessary dependencies and complicate queries, readiness is stored in its own table. This allows for efficient joins with sleep and activity data using time-based queries.

2. **Sleep, Activity, and Heart Rate Stored Separately**
    - Sleep and activity data are stored separately to allow efficient queries and avoid redundant data storage.
    - Heart rate data, which is logged multiple times per day (every 5 minutes or more during workouts), is stored in its own table.
    - The `heartrate` table has optional foreign keys to `daily_sleep` and `daily_activity` when the heart rate measurement is associated with sleep or workouts.

3. **Handling Variable-Resolution Data**  
    - Sleep sessions (which can include naps and interrupted sleep) required special normalization.
    - The `sleep_sessions` table was separated from `daily_sleep`, with a foreign key linking it to `daily_sleep.id`.
    - This approach ensures that irregular sleep patterns are properly captured without redundancy.

4. **Indexing for Performance Optimization**
    - Unique Index on `day` in `daily_sleep`, `daily_activity`, and `daily_readiness`, ensuring only one record per day.
    - Indexes on Foreign Keys:
        - `heartrate.daily_sleep_id` and `heartrate.daily_activity_id` for efficient joins on sleep and activity.
        - `sleep_sessions.daily_sleep_id` to optimize lookups of multiple sleep intervals per day.
    - Indexing Time-Series Data:
        - `heartrate.timestamp` is indexed to allow fast range queries for trends over time.
        - `sleep_sessions.bedtime_start` and `bedtime_end` are indexed for efficient sleep session queries.

5. **Cascade Deletion Constraints for Data Integrity**

    - To prevent orphaned records, the following cascade delete rules were applied:
        - Deleting a `daily_sleep` record will automatically delete:
            - Associated `sleep_sessions` (since they are dependent on `daily_sleep`).
            - `sleep_contributors`, as they are functionally dependent on sleep.
            - `heartrate` records where `daily_sleep_id` is set.

    - Deleting a `daily_activity` record will automatically delete:
        - Associated `activity_contributors`.
        - `heartrate` records where `daily_activity_id` is set.

    - Deleting a `daily_readiness` record will automatically delete:  
        - Associated `readiness_contributors`.

In summary, these design choices will benefit our uses in the following ways:
- **Fully Normalized (3NF)**: Reduces redundancy and ensures efficient updates.  
- **Optimized Query Performance**: Indexing strategies improve speed for time-series lookups and day-based queries.  
- **Data Integrity via Cascading Deletes**: Prevents orphaned records while maintaining meaningful relationships.  
- **Scalability**: The design can accommodate new metrics (e.g., oxygen levels (vO2 Max), workouts) without major schema changes.

---
### Entity Relationship Diagram

<img src="https://github.com/chill0121/Supervised-Sleep/blob/main/database/ERDiagram_Grouped.png?raw=true" alt="ERD" width="800"/>

---
### Schema Details

#### **1. `daily_sleep`**
| Column         | Type     | Constraints         | Description                                  |
|---------------|---------|---------------------|----------------------------------------------|
| id            | UUID    | PRIMARY KEY         | Unique identifier for the sleep record      |
| day           | DATE    | UNIQUE, NOT NULL    | Date of the sleep data                      |
| score         | INT     | NOT NULL            | Overall sleep score                         |
| timestamp     | TIMESTAMP WITH TIME ZONE | NOT NULL | Time when data was recorded                |
| pending       | BOOLEAN | NOT NULL DEFAULT FALSE | Indicates if data is incomplete          |

#### **2. `sleep_contributors`**
| Column          | Type  | Constraints         | Description                                    |
|----------------|------|---------------------|------------------------------------------------|
| sleep_id       | UUID | FOREIGN KEY $\rightarrow$ `daily_sleep(id)` | Links to sleep record      |
| deep_sleep     | INT  | NOT NULL            | Contribution of deep sleep to score            |
| efficiency     | INT  | NOT NULL            | Sleep efficiency                               |
| latency        | INT  | NOT NULL            | Time taken to fall asleep                      |
| rem_sleep      | INT  | NOT NULL            | Contribution of REM sleep                      |
| restfulness    | INT  | NOT NULL            | Restfulness level                             |
| timing         | INT  | NOT NULL            | Sleep timing score                            |
| total_sleep    | INT  | NOT NULL            | Total sleep duration contribution              |

#### **3. `sleep_sessions`**
| Column         | Type     | Constraints | Description |
|--------------|---------|------------|------------------------------------|
| id           | UUID    | PRIMARY KEY | Unique identifier for sleep session |
| daily_sleep_id | UUID  | FOREIGN KEY $\rightarrow$ `daily_sleep(id)` ON DELETE CASCADE | Links to daily sleep summary |
| bedtime_start | TIMESTAMP WITH TIME ZONE | NOT NULL | Sleep session start time |
| bedtime_end   | TIMESTAMP WITH TIME ZONE | NOT NULL | Sleep session end time |
| total_sleep   | INT     | NOT NULL   | Total sleep duration in seconds |
| deep_sleep    | INT     | NOT NULL   | Deep sleep duration (seconds) |
| rem_sleep     | INT     | NOT NULL   | REM sleep duration (seconds) |
| light_sleep   | INT     | NOT NULL   | Light sleep duration (seconds) |
| awake_time    | INT     | NOT NULL   | Time spent awake (seconds) |
| lowest_heart_rate | INT | NOT NULL | Lowest recorded heart rate |

#### **4. `sleep_time_recommendations`**
| Column            | Type     | Constraints         | Description                                   |
|------------------|---------|---------------------|----------------------------------------------|
| id              | UUID    | PRIMARY KEY         | Unique identifier for the sleep time record |
| day             | DATE    | NOT NULL            | Date of recommendation                      |
| optimal_bedtime | TIME    | NULLABLE            | Recommended bedtime                         |
| recommendation  | TEXT    | NOT NULL            | Sleep recommendation (e.g., "earlier bedtime") |

#### **5. `daily_activity`**
| Column         | Type     | Constraints         | Description                                   |
|---------------|---------|---------------------|----------------------------------------------|
| id            | UUID    | PRIMARY KEY         | Unique identifier for the activity record    |
| day           | DATE    | UNIQUE, NOT NULL    | Date of the activity data                   |
| score         | INT     | NOT NULL            | Overall activity score                      |
| active_calories | INT  | NOT NULL            | Calories burned                             |
| steps         | INT     | NOT NULL            | Steps taken                                 |
| equivalent_walking_distance | INT | NOT NULL | Distance walked (in meters)                 |
| high_activity_time | INT | NOT NULL           | Duration of high activity (seconds)         |
| medium_activity_time | INT | NOT NULL         | Duration of medium activity (seconds)       |
| low_activity_time | INT | NOT NULL           | Duration of low activity (seconds)          |
| sedentary_time | INT | NOT NULL              | Duration of sedentary time (seconds)        |

#### **6. `activity_contributors`**
| Column           | Type  | Constraints         | Description                                     |
|-----------------|------|---------------------|-------------------------------------------------|
| activity_id     | UUID | FOREIGN KEY $\rightarrow$ `daily_activity(id)` | Links to activity record |
| meet_daily_targets | INT | NOT NULL | Contribution to activity score |
| move_every_hour | INT | NOT NULL | Movement frequency per hour |
| recovery_time   | INT  | NOT NULL | Recovery time metric |
| stay_active     | INT  | NOT NULL | General activity level |
| training_frequency | INT | NOT NULL | Frequency of training |
| training_volume | INT | NOT NULL | Training volume |

#### **7. `daily_readiness`**
| Column        | Type     | Constraints         | Description                                   |
|--------------|---------|---------------------|----------------------------------------------|
| id           | UUID    | PRIMARY KEY         | Unique identifier for the readiness record  |
| day          | DATE    | UNIQUE, NOT NULL    | Date of readiness data                      |
| score        | INT     | NOT NULL            | Readiness score                             |
| temperature_deviation | FLOAT | NOT NULL | Deviation in body temperature               |
| temperature_trend_deviation | FLOAT | NOT NULL | Trend deviation in body temperature         |

#### **8. `readiness_contributors`**
| Column             | Type  | Constraints         | Description                                    |
|-------------------|------|---------------------|------------------------------------------------|
| readiness_id      | UUID | FOREIGN KEY $\rightarrow$ `daily_readiness(id)` | Links to readiness record |
| activity_balance  | INT  | NOT NULL            | Balance between activity and rest             |
| body_temperature  | INT  | NOT NULL            | Body temperature score                        |
| hrv_balance       | INT  | NOT NULL            | HRV balance contribution                      |
| previous_day_activity | INT | NOT NULL | Activity impact from previous day             |
| previous_night    | INT  | NOT NULL            | Impact of previous night's sleep              |
| recovery_index    | INT  | NOT NULL            | Recovery index metric                         |
| resting_heart_rate | INT | NOT NULL | Resting heart rate                             |
| sleep_balance     | INT  | NOT NULL            | Contribution of sleep balance to readiness    |

#### **9. `heartrate`**
| Column         | Type     | Constraints | Description |
|--------------|---------|------------|-------------------------------------------|
| id           | SERIAL  | PRIMARY KEY | Unique identifier for heart rate record  |
| bpm          | INT     | NOT NULL   | Heart rate in beats per minute |
| source       | TEXT    | NOT NULL   | Measurement source (e.g., "rest", "exercise") |
| timestamp    | TIMESTAMP WITH TIME ZONE | NOT NULL | Time of heart rate measurement |
| daily_sleep_id | UUID  | FOREIGN KEY $\rightarrow$ `daily_sleep(id)` ON DELETE CASCADE | Links to daily sleep summary |
| daily_activity_id | UUID | FOREIGN KEY $\rightarrow$ `daily_activity(id)` ON DELETE CASCADE | Links to daily activity summary |

---
---

### **Relationships**

#### **1:1 (One-to-One) Relationships**
| Parent Table      | Child Table         | Foreign Key              | Relationship Description |
|------------------|--------------------|-------------------------|-------------------------|
| `daily_sleep`    | `sleep_contributors` | `daily_sleep_id` | Each sleep record has one set of contributor scores. |
| `daily_activity` | `activity_contributors` | `daily_activity_id` | Each activity record has one set of contributor scores. |
| `daily_readiness` | `readiness_contributors` | `daily_readiness_id` | Each readiness record has one set of contributor scores. |
| `daily_sleep` | `sleep_time_recommendations` | `daily_sleep_id` | Each day may have a sleep recommendation. |

#### **1:M (One-to-Many) Relationships**
| Parent Table      | Child Table        | Foreign Key              | Relationship Description |
|------------------|-------------------|-------------------------|-------------------------|
| `daily_sleep`    | `sleep_sessions`   | `daily_sleep_id` | One daily sleep record can have multiple sleep sessions (e.g., naps, interrupted sleep). |
| `daily_sleep`    | `heartrate`        | `daily_sleep_id` (nullable) | Some heart rate readings belong to sleep sessions. |
| `daily_activity` | `heartrate`        | `daily_activity_id` (nullable) | Some heart rate readings belong to activity sessions. |

#### **M:M (Many-to-Many) Relationships (Handled via Separate Tables)**
| First Entity      | Second Entity       | Bridge Table          | Description |
|------------------|-------------------|----------------------|-------------|
| `daily_sleep`    | `daily_readiness` | **(Handled via `day` field)** | Readiness depends on previous night’s sleep. |
| `daily_activity` | `daily_readiness` | **(Handled via `day` field)** | Readiness depends on previous day’s activity. |

---

### **Summary of Foreign Key Constraints**
| Table               | Foreign Key           | References             | On Delete Behavior |
|---------------------|----------------------|------------------------|--------------------|
| `sleep_contributors` | `daily_sleep_id`    | `daily_sleep(id)`      | CASCADE |
| `activity_contributors` | `daily_activity_id` | `daily_activity(id)` | CASCADE |
| `readiness_contributors` | `daily_readiness_id` | `daily_readiness(id)` | CASCADE |
| `sleep_sessions`    | `daily_sleep_id`     | `daily_sleep(id)`      | CASCADE |
| `heartrate`         | `daily_sleep_id` | `daily_sleep(id)` | CASCADE |
| `heartrate`         | `daily_activity_id` | `daily_activity(id)` | CASCADE |
| `sleep_time_recommendations` | `daily_sleep_id` | `daily_sleep(id)` | CASCADE |