import psycopg2

daily_sleep = {'daily_sleep': 'id UUID PRIMARY KEY,'
                              'day DATE UNIQUE NOT NULL,'
                              'score INT NOT NULL,'
                              'timestamp TIMESTAMPTZ NOT NULL,'
                              'pending BOOLEAN NOT NULL DEFAULT FALSE'
                              }
sleep_contributors = {'sleep_contributors': 'sleep_id UUID REFERENCES daily_sleep(id) ON DELETE CASCADE,'
                                            'deep_sleep INT NOT NULL,'
                                            'efficiency INT NOT NULL,'
                                            'latency INT NOT NULL,'
                                            'rem_sleep INT NOT NULL,'
                                            'restfulness INT NOT NULL,'
                                            'timing INT NOT NULL,'
                                            'total_sleep INT NOT NULL'
                                            }
sleep_sessions = {'sleep_sessions': 'id UUID PRIMARY KEY,'
                                    'daily_sleep_id UUID REFERENCES daily_sleep(id) ON DELETE CASCADE,'
                                    'bedtime_start TIMESTAMPTZ NOT NULL,'
                                    'bedtime_end TIMESTAMPTZ NOT NULL,'
                                    'total_sleep INT NOT NULL,'
                                    'deep_sleep INT NOT NULL,'
                                    'rem_sleep INT NOT NULL,'
                                    'light_sleep INT NOT NULL,'
                                    'awake_time INT NOT NULL,'
                                    'lowest_heart_rate INT NOT NULL,'
                                    'pending BOOLEAN NOT NULL DEFAULT FALSE'
                                    }
sleep_time_recommendations = {'sleep_time_recommendations': 'id UUID PRIMARY KEY,'
                                                            'day DATE NOT NULL,'
                                                            'optimal_bedtime TIMESTAMP NULL,'
                                                            'recommendation TEXT NOT NULL,'
                                                            'pending BOOLEAN NOT NULL DEFAULT FALSE'
                                                            }
daily_activity = {'daily_activity': 'id UUID PRIMARY KEY,'
                                    'day DATE UNIQUE NOT NULL,'
                                    'score INT NOT NULL,'
                                    'active_calories INT NOT NULL,'
                                    'steps INT NOT NULL,'
                                    'equivalent_walking_distance INT NOT NULL,'
                                    'high_activity_time INT NOT NULL,'
                                    'medium_activity_time INT NOT NULL,'
                                    'low_activity_time INT NOT NULL,'
                                    'sedentary_time INT NOT NULL,'
                                    'pending BOOLEAN NOT NULL DEFAULT FALSE'
                                    }
activity_contributors = {'activity_contributors': 'activity_id UUID REFERENCES daily_activity(id),'
                                                  'meet_daily_targets INT NOT NULL,'
                                                  'move_every_hour INT NOT NULL,'
                                                  'recovery_time INT NOT NULL,'
                                                  'stay_active INT NOT NULL,'
                                                  'training_frequency INT NOT NULL,'
                                                  'training_volume INT NOT NULL'
                                                  }
daily_readiness = {'daily_readiness': 'id UUID PRIMARY KEY,'
                                      'day TIMESTAMP UNIQUE NOT NULL,'
                                      'score INT NOT NULL,'
                                      'temperature_deviation FLOAT NOT NULL,'
                                      'temperature_trend_deviation FLOAT NOT NULL,'
                                      'pending BOOLEAN NOT NULL DEFAULT FALSE'
                                      }
readiness_contributors = {'readiness_contributors': 'readiness_id UUID REFERENCES daily_readiness(id),'
                                                    'activity_balance INT NOT NULL,'
                                                    'body_temperature INT NOT NULL,'
                                                    'hrv_balance INT NOT NULL,'
                                                    'previous_day_activity INT NOT NULL,'
                                                    'previous_night INT NOT NULL,'
                                                    'recovery_index INT NOT NULL,'
                                                    'resting_heart_rate INT NOT NULL,'
                                                    'sleep_balance INT NOT NULL'
                                                    }
heartrate = {'heartrate': 'id SERIAL PRIMARY KEY,'
                          'bpm INT NOT NULL,'
                          'source TEXT NOT NULL,'
                          'timestamp TIMESTAMPTZ NOT NULL,'
                          'daily_sleep_id UUID REFERENCES daily_sleep(id) ON DELETE SET NULL,'
                          'daily_activity_id UUID REFERENCES daily_activity(id) ON DELETE SET NULL,'
                          'pending BOOLEAN NOT NULL DEFAULT FALSE'
                          }
table_list = [daily_sleep, sleep_contributors, sleep_sessions,
              sleep_time_recommendations, daily_activity, activity_contributors,
              daily_readiness, readiness_contributors, heartrate]

def create_table(connection, table_dict):
    """Creates table in database with supplied dictionary {name: columns}, and 
    adds indexes for foreign keys."""
    cursor = connection.cursor()
    table, columns = next(iter(table_dict.items()))
    try:
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {table}({columns});")
        # Extract foreign keys and create indexes.
        index_queries = []
        for col_def in columns.split(","):
            col_parts = col_def.strip().split()
            if "REFERENCES" in col_parts:
                col_name = col_parts[0]  # Get the column name.
                index_name = f"idx_{table}_{col_name}"
                index_queries.append(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table}({col_name});")

        # Execute index creation.
        for query in index_queries:
            cursor.execute(query)

        connection.commit()
    except psycopg2.Error as e:
        connection.rollback()
        print(f"An error has occurred while creating table '{table}': {e}")
    finally:
        cursor.close()

def delete_table(connection, table_name):
    """CASCADE drops table matching input table_name."""
    cursor = connection.cursor()
    try:
        cursor.execute(f'DROP TABLE {table_name} CASCADE;') # NEED TO FIGURE OUT IF CASCADE WORKS WHEN DATA IS IN.
        connection.commit()
    except psycopg2.Error as e:
        connection.rollback()
        print(f"An error has occurred while dropping table '{table_name}': {e}")
    finally:
        cursor.close()