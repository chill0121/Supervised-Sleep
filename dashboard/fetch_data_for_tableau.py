import requests
import pandas as pd
import os
from tableauhyperapi import HyperProcess, Connection, Telemetry, TableDefinition, SqlType, Inserter, CreateMode
from config import settings

# Define API endpoints
API_BASE_URL = "http://0.0.0.0:8000"

ENDPOINTS = {
    "sleep_calendar": f"{API_BASE_URL}/sleep/calendar",
    "heartrate_trends": f"{API_BASE_URL}/heartrate/trends",
    "summary_statistics": f"{API_BASE_URL}/summary/statistics",
    #"stress_trends": f"{API_BASE_URL}/stress_trends"
}

# Create output directory
if not os.path.exists(settings.TAB_DATA_DIR): # Check if directory exists.
    os.makedirs(settings.TAB_DATA_DIR)

# Function to fetch data from API
def fetch_data(endpoint):
    try:
        response = requests.get(endpoint)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data from {endpoint}: {e}")
        return None

# Function to save JSON data as CSV
def save_as_csv(data, filename):
    if data:
        df = pd.DataFrame(data)
        csv_path = os.path.join(settings.TAB_DATA_DIR, f"{filename}.csv")
        df.to_csv(csv_path, index=False)
        print(f"Saved CSV: {csv_path}")

# Function to save JSON data as a Tableau Hyper file
def save_as_hyper(data, filename, table_def):
    hyper_path = os.path.join(settings.TAB_DATA_DIR, f"{filename}.hyper")
    with HyperProcess(telemetry=Telemetry.SEND_USAGE_DATA_TO_TABLEAU) as hyper:
        with Connection(endpoint=hyper.endpoint, database=hyper_path, create_mode=CreateMode.CREATE) as connection:
            connection.catalog.create_table(table_def)
            with Inserter(connection, table_def) as inserter:
                for row in data:
                    inserter.add_row(tuple(row.values()))
                inserter.execute()
    print(f"Saved Hyper file: {hyper_path}")

# Define Hyper table schemas
sleep_calendar_table = TableDefinition("sleep_calendar", [
    TableDefinition.Column("day", SqlType.text()),
    TableDefinition.Column("sleep_score", SqlType.int())
])

heartrate_trends_table = TableDefinition("heartrate_trends", [
    TableDefinition.Column("day", SqlType.text()),
    TableDefinition.Column("avg_heart_rate", SqlType.double()),
    TableDefinition.Column("min_heart_rate", SqlType.int()),
    TableDefinition.Column("max_heart_rate", SqlType.int())
])

summary_statistics_table = TableDefinition("summary_statistics", [
    TableDefinition.Column("day", SqlType.text()),
    TableDefinition.Column("sleep_score", SqlType.int()),
    TableDefinition.Column("activity_score", SqlType.int()),
    TableDefinition.Column("readiness_score", SqlType.int())
])

# stress_trends_table = TableDefinition("stress_trends", [
#     TableDefinition.Column("day", SqlType.text()),
#     TableDefinition.Column("stress_score", SqlType.int())
# ])

# Fetch data and save as CSV and Hyper
for key, endpoint in ENDPOINTS.items():
    data = fetch_data(endpoint)
    if data:
        print(data)
        save_as_csv(data, key)

        # Save as Hyper file
        if key == "sleep_calendar":
            save_as_hyper(data, key, sleep_calendar_table)
        elif key == "heartrate_trends":
            save_as_hyper(data, key, heartrate_trends_table)
        elif key == "summary_statistics":
            save_as_hyper(data, key, summary_statistics_table)
        # elif key == "stress_trends":
        #     save_as_hyper(data, key, stress_trends_table)

print("Data fetching and processing complete.")
