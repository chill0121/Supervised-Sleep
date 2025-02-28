import requests
import json
import os
import logging
from datetime import datetime

# Initialize logging.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load private token for API access.
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
TOKEN_PATH = os.path.join(BASE_DIR, 'config', 'private_token.json')
DATA_DIR = os.path.join(BASE_DIR, 'oura_api', 'data')
TODAY = datetime.today().strftime('%Y-%m-%d')
TODAY_DATETIME = datetime.today().strftime('%Y-%m-%dT%H:%M:%S-08:00')

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
        return '2025-02-03', TODAY # '2023-02-03' beginning date.
    
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

def set_pending_flag(data):
    """
    Indexes through data_batch['data'] to compare dates to TODAY.
    Sets pending flag to True if data batch is incomplete.
    """
    for packet in data['data']:
        # Handles packets that don't have 'day' key.
        if 'day' not in packet:
            packet['pending'] = True if packet['timestamp'][0:10] == TODAY else False
        else:
            packet['pending'] = True if packet['day'] == TODAY else False
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
            set_pending_flag(data_batch[batch])

    file_name = f"{start_date}_to_{end_date}.json"
    file_path = os.path.join(DATA_DIR, file_name)

    with open(file_path, 'w') as fout:
        json.dump(data_batch, fout, indent = 4)

    logging.info(f"Data successfully saved to {file_path}.")