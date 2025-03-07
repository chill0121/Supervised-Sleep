import os
from datetime import datetime

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
TOKEN_PATH = os.path.join(BASE_DIR, 'config', 'private_token.json')
DATA_DIR = os.path.join(BASE_DIR, 'oura_api', 'data')
DB_LOG_DIR = os.path.join(BASE_DIR, 'database', 'db_logs')
TODAY = datetime.today().strftime('%Y-%m-%d')
TODAY_DATETIME = datetime.today().strftime('%Y-%m-%dT%H:%M:%S-08:00')