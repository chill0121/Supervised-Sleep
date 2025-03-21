import os
from datetime import datetime

# File structure constants.
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
TOKEN_PATH = os.path.join(BASE_DIR, 'config', 'private_token.json')
DATA_DIR = os.path.join(BASE_DIR, 'oura_api', 'data')
DB_LOG_DIR = os.path.join(BASE_DIR, 'database', 'db_logs')

# Database Credentials
DB_NAME = 'supervised_sleep'
DB_USER = 'chill'
DB_HOST = 'localhost'
DB_PORT = '5432'