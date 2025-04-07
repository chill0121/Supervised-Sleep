import requests
import pandas as pd
import os
import json
# from tableauhyperapi import HyperProcess, Connection, Telemetry, TableDefinition, SqlType, Inserter, CreateMode # Can't use with Tableau Public (Free) Version
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

def flatten_json(data):
    """Ensure that data is flat and Tableau-readable."""
    # If already a list of flat dicts, return as is
    if all(isinstance(row, dict) for row in data):
        return data
    # Else flatten, or raise an error
    raise ValueError("Data is not flat. Nested structures need to be flattened manually.")

def save_as_json(data: list[dict], filename: str):
    """Save the data to a JSON file."""
    filepath = settings.TAB_DATA_DIR + f"/{filename}.json"
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)
    print(f"Saved {filename}.json to {filepath}")

def generate_tableau_data():
    """Fetches data from API endpoints and saves it as JSON for Tableau Public."""
    for key, url in ENDPOINTS.items():
        print(f"K: {key} | url: {url}")
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            # Validate/flatten structure
            flat_data = flatten_json(data)

            # Save to JSON
            save_as_json(flat_data, key)

        except Exception as e:
            print(f"Failed to fetch or save data from {url}: {e}")

if __name__ == "__main__":
    generate_tableau_data()