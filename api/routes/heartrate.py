from fastapi import APIRouter
from api.db import fetch_query_results

# Handles all heartrate queries.

router = APIRouter(prefix="/heartrate", tags=["Heart Rate Data"])

@router.get("/trends")
def get_heart_rate_trends():
    """Fetch precomputed heart rate trends (3 months)."""
    query = "SELECT * FROM heartrate_trends;"
    return fetch_query_results(query)

@router.get("/custom")
def get_custom_heart_rate(start_date: str, end_date: str):
    """Fetch custom heart rate data."""
    query = """
    SELECT timestamp, bpm FROM heartrate 
    WHERE timestamp BETWEEN %s AND %s
    """
    return fetch_query_results(query, (start_date, end_date))
