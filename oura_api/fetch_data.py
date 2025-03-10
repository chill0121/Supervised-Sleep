import requests
import json
import os
import logging
from datetime import datetime, timedelta
#from config.settings import *

# Initialize logging.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
TOKEN_PATH = os.path.join(BASE_DIR, 'config', 'private_token.json')
DATA_DIR = os.path.join(BASE_DIR, 'oura_api', 'data')
TODAY = datetime.today().strftime('%Y-%m-%d')
TODAY_DATETIME = datetime.today().strftime('%Y-%m-%dT%H:%M:%S-08:00')
START_DATE = '2023-02-03' # Personal hard-coded start date.

def load_token():
    """Load the private token for API access."""
    if not os.path.exists(TOKEN_PATH):
        logging.error("Token file not found. Ensure 'private_token.json' exists.")
        raise FileNotFoundError('Token file not found.')
    
    with open(TOKEN_PATH) as f:
        private_token = json.load(f)
    
    if 'token' not in private_token:
        logging.error("Token file is missing the 'token' key.")
        raise KeyError("Token file is missing the 'token' key.")
    
    return private_token['token']

def get_previous_date_range():
    """Find the previous API pull date range."""
    os.makedirs(DATA_DIR, exist_ok = True)
    data_files = sorted(os.listdir(DATA_DIR))

    # Default start date if no data exists. 
    # Hardcoded based on personal Oura ring start date.
    if not data_files:
        return '2025-02-07', TODAY # '2023-02-03' beginning date.
    
    last_file = data_files[-1]
    last_date = last_file.split('_to_')[-1].split('.json')[0]
    return last_date, TODAY

def fetch_data(batch, headers, params):
    """Fetch data from the API."""
    url = f'https://api.ouraring.com/v2/usercollection/{batch}'
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        logging.info(f'{batch} | Request successful ({response.status_code}).')
        return response.json()
    
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching {batch}: {e}.")
        return None

# def set_pending_flag(data):
#     """
#     Indexes through data_batch['data'] to compare dates to TODAY.
#     Sets pending flag to True if data batch is incomplete.
#     """
#     for packet in data['data']:
#         # Handles packets that don't have 'day' key.
#         if 'day' not in packet:
#             packet['pending'] = True if packet['timestamp'][0:10] == TODAY else False
#         else:
#             packet['pending'] = True if packet['day'] == TODAY else False
#     return None
def set_pending_flag(data, table_name, start_date, end_date):
    """
    Sets the 'pending' flag for data that belongs to TODAY.
    Handles missing 'day' or 'timestamp' keys safely and logs any missing data.

    Args:
        data (dict): The batch of data to process.
        table_name (str): Name of the table for logging.
        start_date (str): The start date of the data batch.
        end_date (str): The end date of the data batch.
    """
    if 'data' not in data or not isinstance(data['data'], list):
        logging.warning(f"Missing data for table '{table_name}' from {start_date} to {end_date}.")
        return

    for packet in data['data']:
        # Check for missing keys before setting pending flag
        if 'day' in packet:
            packet['pending'] = packet['day'] == TODAY
        elif 'timestamp' in packet:
            packet['pending'] = packet['timestamp'][:10] == TODAY
        else:
            logging.warning(f"Missing 'day' or 'timestamp' in {table_name} entry from {start_date} to {end_date}. Skipping entry.")

    return None

def fetch_process_save_data():
    """Main API function to pull API data and save it to JSON."""
    token = load_token()
    start_date, end_date = get_previous_date_range()

    headers = {'Authorization': f"Bearer {token}"}
    params = {'start_date': start_date, 'end_date': end_date}

    data_batch = {batch: [] for batch in [
        'daily_sleep', 'daily_activity', 'daily_readiness', 'daily_resilience',
        'daily_stress', 'daily_spo2', 'heartrate', 'rest_mode_period', 'sleep',
        'sleep_time', 'vO2_max', 'workout'
        ]}
    # Iterate through data_batch for API pull.
    for batch in data_batch:
        # Special handling for heartrate, requires datetime.
        params_datetime = {
            'start_datetime': start_date + 'T00:00:00-08:00', 
            'end_datetime': TODAY_DATETIME
            }
        data = fetch_data(batch, headers, params_datetime if batch == 'heartrate' else params)
        # if batch == 'heartrate':
        #     data = fetch_data(batch, headers, params_datetime)
        # else:
        #     data = fetch_data(batch, headers, params)

        if data:
            data_batch[batch] = data
            set_pending_flag(data_batch[batch], batch, start_date, end_date)

    file_name = f"{start_date}_to_{end_date}.json"
    file_path = os.path.join(DATA_DIR, file_name)

    with open(file_path, 'w') as fout:
        json.dump(data_batch, fout, indent = 4)

    logging.info(f"Data successfully saved to {file_path}.")

def save_data(data_batch, start_date, end_date):
    """Save data batch to JSON file."""
    os.makedirs(DATA_DIR, exist_ok=True)
    file_name = f"{start_date}_to_{end_date}.json"
    file_path = os.path.join(DATA_DIR, file_name)

    with open(file_path, 'w') as fout:
        json.dump(data_batch, fout, indent=4)

    logging.info(f"Data successfully saved to {file_path}.")

def fetch_historical_data():
    """
    Fetch all historical Oura data in 15-day increments to limit API issues.
    This should be run once to initialize the database and then use fetch_process_save_data().
    """
    token = load_token()
    headers = {'Authorization': f"Bearer {token}"}

    start_date = datetime.strptime(START_DATE, "%Y-%m-%d")
    end_date = datetime.strptime(TODAY, "%Y-%m-%d")

    while start_date < end_date:
        batch_end_date = min(start_date + timedelta(days=14), end_date)  # 15-day increments
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = batch_end_date.strftime("%Y-%m-%d")

        logging.info(f"Fetching historical data from {start_str} to {end_str}...")

        params = {'start_date': start_str, 'end_date': end_str}

        data_batch = {batch: [] for batch in [
            'daily_sleep', 'daily_activity', 'daily_readiness', 'daily_resilience',
            'daily_stress', 'daily_spo2', 'heartrate', 'rest_mode_period', 'sleep',
            'sleep_time', 'vO2_max', 'workout'
        ]}

        for batch in data_batch:
            params_datetime = {'start_datetime': start_str + 'T00:00:00-08:00', 'end_datetime': end_str + 'T23:59:59-08:00'}
            data = fetch_data(batch, headers, params_datetime if batch == 'heartrate' else params)

            if data:
                set_pending_flag(data, batch, start_str, end_str)  # Pass additional parameters
                data_batch[batch] = data
        # for batch in data_batch:
        #     params_datetime = {'start_datetime': start_str + 'T00:00:00-08:00', 'end_datetime': end_str + 'T23:59:59-08:00'}
        #     data = fetch_data(batch, headers, params_datetime if batch == 'heartrate' else params)

        #     if data:
        #         data_batch[batch] = data
        #         set_pending_flag(data_batch[batch])

        save_data(data_batch, start_str, end_str)

        # Move to next 15-day interval
        start_date = batch_end_date + timedelta(days=1)

if __name__ == '__main__':
    fetch_process_save_data()