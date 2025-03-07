import psycopg2
from psycopg2.extras import execute_values
import logging
import os
from config.settings import * #BASE_DIR, TOKEN_PATH, DATA_DIR, TODAY, TODAY_DATETIME, DB_LOG_DIR
import json

# Initialize logging.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Database credentials
DB_NAME = 'supervised_sleep'
DB_USER = 'chill'
DB_HOST = 'localhost'
DB_PORT = '5432'

table_dict = {'daily_sleep': 'id UUID PRIMARY KEY,'
                              'day DATE UNIQUE NOT NULL,'
                              'score INT NOT NULL,'
                              'timestamp TIMESTAMPTZ NOT NULL,'
                              'pending BOOLEAN NOT NULL DEFAULT FALSE',
              'sleep_contributors': 'sleep_id UUID PRIMARY KEY REFERENCES daily_sleep(id) ON DELETE CASCADE,'
                                    'deep_sleep INT NOT NULL,'
                                    'efficiency INT NOT NULL,'
                                    'latency INT NOT NULL,'
                                    'rem_sleep INT NOT NULL,'
                                    'restfulness INT NOT NULL,'
                                    'timing INT NOT NULL,'
                                    'total_sleep INT NOT NULL',
              'sleep_sessions': 'id UUID PRIMARY KEY,'
                                'daily_sleep_id UUID REFERENCES daily_sleep(id) ON DELETE CASCADE,'
                                'bedtime_start TIMESTAMPTZ NOT NULL,'
                                'bedtime_end TIMESTAMPTZ NOT NULL,'
                                'total_sleep_duration INT NOT NULL,'
                                'deep_sleep_duration INT NOT NULL,'
                                'rem_sleep_duration INT NOT NULL,'
                                'light_sleep_duration INT NOT NULL,'
                                'awake_time INT NOT NULL,'
                                'lowest_heart_rate INT NOT NULL,'
                                'latency INT NOT NULL,'
                                'efficiency INT NOT NULL,'
                                'average_breath FLOAT NOT NULL,'
                                'average_heart_rate INT NULL,'
                                'average_hrv INT NULL,'
                                #'movement_30_sec TEXT NOT NULL,'
                                'restless_periods INT NOT NULL,'
                                'period INT NOT NULL,'
                                'sleep_phase_5_min TEXT NOT NULL,'
                                'time_in_bed INT NOT NULL,'
                                'sleep_score_delta INT NULL,'
                                'low_battery_alert BOOLEAN NOT NULL DEFAULT FALSE,'
                                #'sleep_algorithm_version TEXT NOT NULL,'
                                'type TEXT NOT NULL,'
                                'pending BOOLEAN NOT NULL DEFAULT FALSE',
              'sleep_time_recommendations': 'id UUID PRIMARY KEY,'
                                            'day DATE NOT NULL,'
                                            'optimal_bedtime TIMESTAMP NULL,'
                                            'recommendation TEXT NOT NULL,'
                                            'pending BOOLEAN NOT NULL DEFAULT FALSE',
              'daily_activity': 'id UUID PRIMARY KEY,'
                                'day DATE UNIQUE NOT NULL,'
                                'score INT NOT NULL,'
                                'active_calories INT NOT NULL,'
                                'steps INT NOT NULL,'
                                'equivalent_walking_distance INT NOT NULL,'
                                'high_activity_time INT NOT NULL,'
                                'medium_activity_time INT NOT NULL,'
                                'low_activity_time INT NOT NULL,'
                                'sedentary_time INT NOT NULL,'
                                'average_met_minutes FLOAT NOT NULL,'
                                'high_activity_met_minutes INT NOT NULL,'
                                'medium_activity_met_minutes INT NOT NULL,'
                                'low_activity_met_minutes INT NOT NULL,'
                                'sedentary_met_minutes INT NOT NULL,'
                                'timestamp TIMESTAMPTZ NOT NULL,'
                                'pending BOOLEAN NOT NULL DEFAULT FALSE',
              'activity_contributors': 'activity_id UUID PRIMARY KEY REFERENCES daily_activity(id),'
                                       'meet_daily_targets INT NOT NULL,'
                                       'move_every_hour INT NOT NULL,'
                                       'recovery_time INT NOT NULL,'
                                       'stay_active INT NOT NULL,'
                                       'training_frequency INT NOT NULL,'
                                       'training_volume INT NOT NULL',
              'daily_readiness': 'id UUID PRIMARY KEY,'
                                 'day TIMESTAMP UNIQUE NOT NULL,'
                                 'score INT NOT NULL,'
                                 'temperature_deviation FLOAT NOT NULL,'
                                 'temperature_trend_deviation FLOAT NULL,'
                                 'pending BOOLEAN NOT NULL DEFAULT FALSE',
              'readiness_contributors': 'readiness_id UUID PRIMARY KEY REFERENCES daily_readiness(id),'
                                        'activity_balance INT NOT NULL,'
                                        'body_temperature INT NOT NULL,'
                                        'hrv_balance INT NOT NULL,'
                                        'previous_day_activity INT NULL,'
                                        'previous_night INT NOT NULL,'
                                        'recovery_index INT NOT NULL,'
                                        'resting_heart_rate INT NOT NULL,'
                                        'sleep_balance INT NOT NULL',
              'heartrate': 'id SERIAL PRIMARY KEY,'
                           'bpm INT NOT NULL,'
                           'source TEXT NOT NULL,'
                           'timestamp TIMESTAMPTZ NOT NULL,'
                           'daily_sleep_id UUID REFERENCES daily_sleep(id) ON DELETE SET NULL,'
                           'daily_activity_id UUID REFERENCES daily_activity(id) ON DELETE SET NULL,'
                           'pending BOOLEAN NOT NULL DEFAULT FALSE'
              }

def create_table(connection, table_dict):
    """Creates table in database with supplied dictionary {name: columns}, and 
    adds indexes for foreign keys."""
    cursor = connection.cursor()
    table, columns = next(iter(table_dict.items()))
    try:
        # First check if the table exists for logging.
        cursor.execute(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}');")
        table_exists = cursor.fetchone()[0]
        # Only log if the table didn't exist before.
        if not table_exists:
            logging.info(f"Creating {table}.")
        # Create table.
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {table}({columns});")
        # Index creation: extract foreign keys and create indexes.
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
        logging.error(f"An error has occurred while creating table '{table}': {e}")
    finally:
        cursor.close()

def delete_table(connection, table_name):
    """CASCADE drops table matching input table_name."""
    cursor = connection.cursor()
    try:
        cursor.execute(f'DROP TABLE {table_name} CASCADE;') # NEED TO TEST CASCADE WHEN DATA IS IN.
        connection.commit()
        logging.info(f"Table {table_name} dropped successfully.")
    except psycopg2.Error as e:
        connection.rollback()
        logging.error(f"An error has occurred while dropping table '{table_name}': {e}")
    finally:
        cursor.close()

def log_removed_columns(table_name, removed_columns):
    """Logs removed columns while ensuring no redundancy."""
    log_path = os.path.join(DB_LOG_DIR, 'removed_columns_log.txt')

    # Initialize the existing logs as an empty dictionary
    existing_logs = {}

    # If the log file exists and has data, load the existing log entries
    if os.path.exists(log_path) and os.path.getsize(log_path) > 0:
        with open(log_path, 'r') as log_file:
            for line in log_file:
                line = line.strip()
                if ': ' in line:
                    table, columns = line.split(': ')
                    existing_logs[table] = set(columns.split(', '))

    # Add only new columns, ensuring no duplicates for the current table
    if table_name not in existing_logs:
        existing_logs[table_name] = set(removed_columns)
    else:
        existing_logs[table_name].update(removed_columns)

    # Write the updated log without redundancy, skipping empty columns
    with open(log_path, 'w') as log_file:
        for table, columns in sorted(existing_logs.items()):
            if columns:  # Only write if there are columns to log
                log_file.write(f"{table}: {', '.join(sorted(columns))}\n")

removed_columns_global = {}  # Dictionary to store removed columns for all tables

def clean_data(data, valid_columns, table_name):
    """Removes columns not in schema and stores them in a global variable to reduce redundancy."""
    removed_columns = set()
    cleaned_data = []
    
    for record in data:
        valid_record = {key: value for key, value in record.items() if key in valid_columns}
        removed_columns.update(set(record.keys()) - set(valid_record.keys()))
        cleaned_data.append(valid_record)

    # Log removed columns for reference, will store them in another function.
    if removed_columns:
        removed_columns_global[table_name] = removed_columns

    return cleaned_data

def log_all_removed_columns():
    """Logs all removed columns at once instead of repeatedly in `clean_data()`."""
    for table_name, removed_columns in removed_columns_global.items():
        log_removed_columns(table_name, removed_columns)

def bulk_insert_data(cursor, table_name, data, batch_size=500):
    """Efficiently inserts multiple records in batches."""
    if not data:
        return

    cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}';")
    valid_columns = {row[0] for row in cursor.fetchall()}
    #logging.info(f"Data being processed for {table_name}: {data}")
    cleaned_data = clean_data(data, valid_columns, table_name)
    if not cleaned_data:
        return

    columns = list(cleaned_data[0].keys())
    # Get the primary key of the table dynamically
    cursor.execute(f"""
        SELECT column_name 
        FROM information_schema.key_column_usage 
        WHERE table_name = '{table_name}'
          AND constraint_name = '{table_name}_pkey';
    """)
    primary_key = cursor.fetchone()
    # Only use ON CONFLICT if a primary key exists
    conflict_clause = f"ON CONFLICT ({primary_key[0]}) DO NOTHING" if primary_key else ""

    query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES %s {conflict_clause};"
    # query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES %s ON CONFLICT ({columns[0]}) DO NOTHING;"

    for i in range(0, len(cleaned_data), batch_size):
        batch = cleaned_data[i : i + batch_size]
        values = [[record[col] for col in columns] for record in batch]  # Ensure correct format
        try:
            execute_values(cursor, query, values)  # Properly pass values
        except psycopg2.Error as e:
            logging.error(f"Error inserting batch into '{table_name}': {e}")

def update_pending_data(cursor, table_name, data, condition):
    """Updates pending data when a full version is available."""
    updates = ', '.join([f"{key} = %s" for key in data.keys()])
    query = f"UPDATE {table_name} SET {updates} WHERE {condition} AND pending = TRUE;"
    
    try:
        cursor.execute(query, tuple(data.values()))
    except psycopg2.Error as e:
        logging.error(f"Error updating pending data in '{table_name}': {e}")

def is_file_already_uploaded(filename):
    """Check/Create dir and log file for previously processed API data. Reads log."""
    if not os.path.exists(DB_LOG_DIR): # Check if directory exists.
        os.makedirs(DB_LOG_DIR)
    db_log_path = os.path.join(DB_LOG_DIR, 'insert_db_log.txt')
    if not os.path.exists(db_log_path):  # Check if file exists.
        with open(db_log_path, 'w') as log_file:
            logging.info(f'Log file "{db_log_path}" created.')

    with open(db_log_path, 'r') as log_file:
        uploaded_files = log_file.readlines()
    return filename + '\n' in uploaded_files

def mark_file_as_uploaded(filename, db_log_path):
    """Writes to log filenames that have been processed and inserted. """
    with open(db_log_path, 'a') as log_file:
        log_file.write(filename + '\n')

def get_unprocessed_json_files():
    """Checks which files have been previously processed and inserted into database.
    Returns: List('file_names')"""
    # List all files in the folder
    files_to_upload = []
    for filename in os.listdir(DATA_DIR):
        if filename.endswith('.json'):  # Only consider .json files
            if not is_file_already_uploaded(filename):
                files_to_upload.append(filename)
                # # If the file has not been uploaded, load and process it
                # with open(os.path.join(DATA_DIR, filename), 'r') as file:
                #     data = json.load(file)
    return files_to_upload

def insert_json_files_to_db(connection, data_batch):
    """Inserts API data.json files into the database. Calls insert_data() and update_pending_data()."""
    try:
        cursor = connection.cursor()
        files_to_upload = sorted(get_unprocessed_json_files()) #Sorted to ensure chronology.
        for filename in files_to_upload:
            with open(os.path.join(DATA_DIR,filename), 'r') as file:
                data_batch = json.load(file)
            logging.info(f"Inserting {filename} data into database.")
            # Handle tables that have one row per day.
            # Define correct foreign key names for each contributors table
            contributor_foreign_keys = {'daily_sleep': 'sleep_id',
                                        'daily_activity': 'activity_id',
                                        'daily_readiness': 'readiness_id'
                                        }
            daily_sleep_map = {}  # {day: daily_sleep.id}
            # Insert daily tables first
            for table in ['daily_sleep', 'daily_activity', 'daily_readiness']:
                if table in data_batch and data_batch[table]['data']:
                    for record in data_batch[table]['data']:
                        contributors = record.pop('contributors', None)  # Extract contributors
                        # Map `day` to `id` for later reference in `sleep_sessions`
                        if table == 'daily_sleep':
                            daily_sleep_map[record['day']] = record['id']
                        bulk_insert_data(cursor, table, [record])  # Insert main record
                    
                        # If contributors exist, insert into the related table
                        if contributors:
                            contributors_table = f"{table.replace('daily_', '')}_contributors"
                            contributors[contributor_foreign_keys[table]] = record['id']  # Set correct foreign key
                            bulk_insert_data(cursor, contributors_table, [contributors])
            # Insert sleep sessions and reference correct 'daily_sleep' id by using 'day'.
            if 'sleep' in data_batch and data_batch['sleep']['data']:
                sleep_sessions_records = []

                for session in data_batch['sleep']['data']:
                    sleep_session = session.copy()  # Preserve original JSON structure
                    
                    # Find correct `daily_sleep_id` using `day`
                    session_day = sleep_session['day']
                    sleep_session['daily_sleep_id'] = daily_sleep_map.get(session_day, None)

                    if sleep_session['daily_sleep_id'] is None:
                        logging.warning(f"Warning: No matching daily_sleep record for sleep session on {session_day}. Skipping...")
                        continue  # Skip if no matching daily_sleep_id

                    sleep_sessions_records.append(sleep_session)

                bulk_insert_data(cursor, "sleep_sessions", sleep_sessions_records)

            # Handle heart rate (can link to sleep or activity)
            if 'heartrate' in data_batch and data_batch['heartrate']['data']:

                bulk_insert_data(cursor, 'heartrate', data_batch['heartrate']['data'])
            # Commit changes.
            connection.commit()
            mark_file_as_uploaded(filename, os.path.join(DB_LOG_DIR, 'insert_db_log.txt'))
            logging.info(f"Data inserted into the database successfully.")
        # Log all removed columns now that processing is done.
        log_all_removed_columns()

    except psycopg2.Error as e:
        connection.rollback()
        logging.error(f"Error inserting data to database: {e}")
    finally:
        cursor.close()